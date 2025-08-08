from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date, time, datetime, timedelta
import itertools
from app.models.table import Table
from app.models.reservation import Reservation, ReservationTable
from app.schemas.reservation import TableAssignment, TimeSlot
from sqlalchemy import func
from app.models.table_layout import TableLayout
from app.models.availability_block import AvailabilityBlock, BlockScope, BlockType, Recurrence


class TableService:
    def __init__(self, db: Session):
        self.db = db

    def get_available_tables(
        self, 
        room_id: str, 
        date: date, 
        time: time,
        party_size: int,
        duration_hours: int = 2,
        exclude_reservation_id: str = None,
        include_non_public: bool = False,
        exclude_table_ids: Optional[List[str]] = None
    ) -> List[Table]:
        """Get all available tables for a given room, date, and time slot"""
        print(f"DEBUG: Getting available tables for room {room_id} with proper conflict checking")
        print(f"DEBUG: Date: {date}, Time: {time}, Party size: {party_size}")
        
        # Apply availability blocks (room/global) for blackout and release rules
        if self._is_room_blocked(room_id, date, time):
            return []

        # Get all tables in the room
        query = self.db.query(Table).filter(
            and_(
                Table.room_id == room_id,
                Table.active == True
            )
        )
        if not include_non_public:
            query = query.filter(Table.public_bookable == True)
        all_tables = query.all()
        
        # Get reserved table IDs for this time slot (with duration overlap checking)
        reserved_table_ids = self.get_reserved_table_ids_with_duration(date, time, duration_hours, exclude_reservation_id)
        
        # Filter out reserved tables and table-level blocks
        exclude_table_ids = set(exclude_table_ids or [])
        available_tables = [
            table for table in all_tables
            if str(table.id) not in reserved_table_ids and str(table.id) not in exclude_table_ids
            and not self._is_table_blocked(str(table.id), date, time)
        ]
        
        print(f"DEBUG: Found {len(all_tables)} total tables, {len(reserved_table_ids)} reserved, {len(available_tables)} available")
        return available_tables

    def get_available_tables_all_rooms(
        self, 
        date: date, 
        time: time,
        party_size: int,
        duration_hours: int = 2,
        exclude_reservation_id: str = None,
        include_non_public: bool = False,
        exclude_table_ids: Optional[List[str]] = None
    ) -> List[Table]:
        """Get all available tables across all active rooms for a given date and time slot"""
        print(f"DEBUG: Getting available tables from all rooms with proper conflict checking")
        print(f"DEBUG: Date: {date}, Time: {time}, Party size: {party_size}")
        
        # Get all tables across all active rooms
        from app.models.room import Room
        query = self.db.query(Table).join(Room).filter(
            and_(
                Table.active == True,
                Room.active == True
            )
        )
        if not include_non_public:
            query = query.filter(Table.public_bookable == True)
        all_tables = query.all()
        
        # Get reserved table IDs for this time slot (with duration overlap checking)
        reserved_table_ids = self.get_reserved_table_ids_with_duration(date, time, duration_hours, exclude_reservation_id)
        
        # Filter out reserved tables
        exclude_table_ids = set(exclude_table_ids or [])
        available_tables = [
            table for table in all_tables
            if str(table.id) not in reserved_table_ids and str(table.id) not in exclude_table_ids
        ]
        
        print(f"DEBUG: Found {len(all_tables)} total tables, {len(reserved_table_ids)} reserved, {len(available_tables)} available")
        return available_tables

    def find_best_table_combination(
        self, 
        room_id: Optional[str], 
        date: date, 
        time: time,
        party_size: int,
        duration_hours: int = 2,
        include_non_public: bool = True,
        exclude_table_ids: Optional[List[str]] = None
    ) -> Optional[List[Table]]:
        """
        Find the best combination of tables for a party size.
        If room_id is None, searches across all active rooms with room preference.
        Returns the combination with smallest excess seats and fewest tables.
        """
        if room_id:
            # Search in specific room only
            available_tables = self.get_available_tables(
                room_id, date, time, party_size, duration_hours,
                include_non_public=include_non_public,
                exclude_table_ids=exclude_table_ids
            )
            return self._find_best_combination_in_tables(available_tables, party_size)
        else:
            # Search across all active rooms with room preference
            return self._find_best_combination_across_rooms(
                date, time, party_size, duration_hours, include_non_public, exclude_table_ids
            )
    
    def _find_best_combination_in_tables(self, available_tables: List[Table], party_size: int) -> Optional[List[Table]]:
        """Find best table combination within a given set of tables"""
        if not available_tables:
            return None

        # Get combinable tables only
        combinable_tables = [t for t in available_tables if t.combinable]
        
        if not combinable_tables:
            # If no combinable tables, check if any single table can accommodate
            for table in available_tables:
                if table.capacity >= party_size:
                    return [table]
            return None

        # Try single tables first
        for table in combinable_tables:
            if table.capacity >= party_size:
                return [table]

        # Try combinations of tables - IMPORTANT: Only combine tables from the same room!
        best_combination = None
        best_score = float('inf')

        # Group tables by room to ensure we don't mix rooms
        tables_by_room = {}
        for table in combinable_tables:
            room_id = table.room_id
            if room_id not in tables_by_room:
                tables_by_room[room_id] = []
            tables_by_room[room_id].append(table)

        def _fetch_layouts(tables: List[Table]) -> dict:
            table_ids = [str(t.id) for t in tables]
            layouts = (
                self.db.query(TableLayout)
                .filter(TableLayout.table_id.in_(table_ids))
                .all()
            )
            return {str(l.table_id): l for l in layouts}

        def _distance(a: TableLayout, b: TableLayout) -> float:
            ax = (a.x_position or 0) + (a.width or 0) / 2.0
            ay = (a.y_position or 0) + (a.height or 0) / 2.0
            bx = (b.x_position or 0) + (b.width or 0) / 2.0
            by = (b.y_position or 0) + (b.height or 0) / 2.0
            return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5

        def _is_combo_connected(combo: List[Table], layouts_by_id: dict) -> bool:
            # Build adjacency graph using explicit connections or proximity
            ADJACENT_DISTANCE_PX = 150.0
            ids = [str(t.id) for t in combo]
            # adjacency list
            graph = {i: set() for i in ids}
            for i in range(len(combo)):
                for j in range(i + 1, len(combo)):
                    ti = combo[i]
                    tj = combo[j]
                    li = layouts_by_id.get(str(ti.id))
                    lj = layouts_by_id.get(str(tj.id))
                    connected = False
                    if li and lj:
                        if _distance(li, lj) <= ADJACENT_DISTANCE_PX:
                            connected = True
                        # Explicit linked tables also count
                        if not connected:
                            if (li.connected_to and str(li.connected_to) == str(lj.id)) or (
                                lj.connected_to and str(lj.connected_to) == str(li.id)
                            ) or li.is_connected or lj.is_connected:
                                connected = True
                    # If no layout info, fall back to allowing connection
                    if not li or not lj:
                        connected = connected or False
                    if connected:
                        graph[ids[i]].add(ids[j])
                        graph[ids[j]].add(ids[i])
            # BFS to check connected component size
            if not ids:
                return False
            visited = set([ids[0]])
            stack = [ids[0]]
            while stack:
                cur = stack.pop()
                for nxt in graph[cur]:
                    if nxt not in visited:
                        visited.add(nxt)
                        stack.append(nxt)
            return len(visited) == len(ids)

        # Try combinations within each room
        for room_id, room_tables in tables_by_room.items():
            # Fetch layouts once per room
            layouts_by_id = _fetch_layouts(room_tables)
            # Try combinations of 2 to 6 tables (slightly higher cap) within the same room
            for r in range(2, min(7, len(room_tables) + 1)):
                for combo in itertools.combinations(room_tables, r):
                    total_capacity = sum(table.capacity for table in combo)
                    if total_capacity < party_size:
                        continue
                    # Ensure the combo is spatially connected/adjacent
                    if not _is_combo_connected(list(combo), layouts_by_id):
                        continue
                    # Score: excess seats + number of tables (weighted)
                    excess_seats = total_capacity - party_size
                    num_tables = len(combo)
                    score = excess_seats + (num_tables * 0.1)
                    if score < best_score:
                        best_score = score
                        best_combination = list(combo)

        return best_combination
    
    def _find_best_combination_across_rooms(self, date: date, time: time, party_size: int, duration_hours: int = 2, include_non_public: bool = False, exclude_table_ids: Optional[List[str]] = None) -> Optional[List[Table]]:
        """Find best table combination across all rooms, preferring same-room combinations"""
        from app.models.room import Room
        
        # Get all active rooms
        active_rooms = self.db.query(Room).filter(Room.active == True).all()
        
        best_combination = None
        best_score = float('inf')
        
        # First, try to find combinations within each room
        for room in active_rooms:
            room_tables = self.get_available_tables(
                room.id, date, time, party_size, duration_hours,
                include_non_public=include_non_public,
                exclude_table_ids=exclude_table_ids
            )
            room_combo = self._find_best_combination_in_tables(room_tables, party_size)
            
            if room_combo:
                total_capacity = sum(table.capacity for table in room_combo)
                excess_seats = total_capacity - party_size
                num_tables = len(room_combo)
                score = excess_seats + (num_tables * 0.1)  # Small penalty for more tables
                
                if score < best_score:
                    best_score = score
                    best_combination = room_combo
        
        # If no single-room combination found, try cross-room combinations
        if not best_combination:
            all_tables = self.get_available_tables_all_rooms(
                date, time, party_size, duration_hours,
                include_non_public=include_non_public,
                exclude_table_ids=exclude_table_ids
            )
            best_combination = self._find_best_combination_in_tables(all_tables, party_size)
        
        return best_combination

    def get_availability_for_date(
        self, 
        room_id: str, 
        date: date, 
        party_size: int,
        duration_hours: int = 2,
        include_non_public: bool = False
    ) -> List[TimeSlot]:
        """Get available time slots for a given date and party size"""
        from app.core.config import settings
        
        time_slots = []
        
        # Generate time slots from opening to closing hour
        for hour in range(settings.OPENING_HOUR, settings.CLOSING_HOUR):
            for minute in [0, 30]:  # 30-minute intervals
                time_slot = time(hour, minute)
                
                # Check if tables are available for this time slot
                available_tables = self.get_available_tables(
                    room_id, date, time_slot, party_size, duration_hours, include_non_public=include_non_public
                )
                
                if available_tables:
                    # Find best combination
                    best_combo = self.find_best_table_combination(
                        room_id, date, time_slot, party_size, duration_hours, include_non_public=include_non_public
                    )
                    
                    if best_combo:
                        table_assignments = [
                            TableAssignment(
                                table_id=str(table.id),
                                table_name=table.name,
                                capacity=table.capacity
                            ) for table in best_combo
                        ]
                        
                        total_capacity = sum(table.capacity for table in best_combo)
                        
                        time_slots.append(TimeSlot(
                            time=time_slot,
                            available_tables=table_assignments,
                            total_capacity=total_capacity
                        ))
        
        return time_slots

    def assign_tables_to_reservation(
        self, 
        reservation_id: str, 
        table_ids: List[str]
    ) -> List[ReservationTable]:
        """Assign tables to a reservation"""
        reservation_tables = []
        
        for table_id in table_ids:
            reservation_table = ReservationTable(
                reservation_id=reservation_id,
                table_id=table_id
            )
            self.db.add(reservation_table)
            reservation_tables.append(reservation_table)
        
        self.db.commit()
        return reservation_tables

    def get_reserved_table_ids(self, date: date, time: time, exclude_reservation_id: str = None) -> List[str]:
        """Get list of table IDs that are reserved at the given date and time"""
        from app.models.reservation import ReservationStatus, Reservation
        
        query = self.db.query(Reservation).filter(
            and_(
                Reservation.date == date,
                Reservation.time == time,
                Reservation.status != ReservationStatus.CANCELLED
            )
        )
        
        # Exclude a specific reservation if provided (useful for editing)
        if exclude_reservation_id:
            query = query.filter(Reservation.id != exclude_reservation_id)
        
        reservations = query.all()
        
        reserved_table_ids = []
        for reservation in reservations:
            table_assignments = self.db.query(ReservationTable).filter(
                ReservationTable.reservation_id == reservation.id
            ).all()
            
            for assignment in table_assignments:
                reserved_table_ids.append(str(assignment.table_id))
        
        return reserved_table_ids
    
    def get_reserved_table_ids_with_duration(self, date: date, time: time, duration_hours: int = 2, exclude_reservation_id: str = None) -> List[str]:
        """Get table IDs that are reserved for a given time slot with duration overlap checking"""
        # Calculate the end time for the reservation
        start_datetime = datetime.combine(date, time)
        end_datetime = start_datetime + timedelta(hours=duration_hours)
        
        # Get all reservations that overlap with this time slot
        overlapping_reservations = self.db.query(Reservation).filter(
            and_(
                Reservation.date == date,
                Reservation.status.in_(['confirmed']),  # Only confirmed reservations
                Reservation.id != exclude_reservation_id if exclude_reservation_id else True
            )
        ).all()
        
        # Check for time overlap
        reserved_table_ids = []
        for reservation in overlapping_reservations:
            reservation_start = datetime.combine(reservation.date, reservation.time)
            reservation_end = reservation_start + timedelta(hours=reservation.duration_hours)
            
            # Check if there's any overlap
            if (start_datetime < reservation_end and end_datetime > reservation_start):
                # Get table IDs for this reservation
                reservation_tables = self.db.query(ReservationTable).filter(
                    ReservationTable.reservation_id == reservation.id
                ).all()
                reserved_table_ids.extend([str(rt.table_id) for rt in reservation_tables])
        
        return list(set(reserved_table_ids))  # Remove duplicates

    def _get_room_capacity(self, room_id: str) -> int:
        """Get the total capacity of all active tables in a room"""
        total_capacity = self.db.query(Table).filter(
            and_(
                Table.room_id == room_id,
                Table.active == True
            )
        ).with_entities(func.sum(Table.capacity)).scalar()
        
        return total_capacity or 0 

    # --- Availability Blocks Helpers ---
    def _is_within_blackout(self, start_dt, end_dt, date, time) -> bool:
        if not start_dt or not end_dt:
            return False
        from datetime import datetime
        target = datetime.combine(date, time)
        return start_dt <= target < end_dt

    def _is_under_release(self, block: AvailabilityBlock, date, time) -> bool:
        if block.block_type != BlockType.RELEASE:
            return False
        # Weekly release: hide same-day until release_time
        if block.recurrence == Recurrence.WEEKLY and block.weekdays and block.release_time:
            try:
                weekday = date.weekday()  # 0=Mon
                weekdays = [int(x) for x in block.weekdays.split(',') if x.strip().isdigit()]
                if weekday in weekdays:
                    # If current date equals target date and now < release_time in TZ -> block
                    import pytz
                    from datetime import datetime
                    tz = pytz.timezone(block.timezone or 'Europe/Berlin')
                    now_local = datetime.now(tz)
                    # compare only if now is same day as target in that TZ
                    target_local_date = now_local.date()
                    if target_local_date == date:
                        # Build today release datetime
                        release_dt = tz.localize(datetime(now_local.year, now_local.month, now_local.day, block.release_time.hour, block.release_time.minute))
                        if now_local < release_dt:
                            return True
            except Exception:
                return False
        return False

    def _active_blocks(self):
        return self.db.query(AvailabilityBlock).filter(AvailabilityBlock.active == True).all()

    def _is_room_blocked(self, room_id: str, date, time) -> bool:
        for b in self._active_blocks():
            if b.scope == BlockScope.GLOBAL:
                if (b.block_type == BlockType.BLACKOUT and self._is_within_blackout(b.start_datetime, b.end_datetime, date, time)) or self._is_under_release(b, date, time):
                    return True
            if b.scope == BlockScope.ROOM and b.target_id == str(room_id):
                if (b.block_type == BlockType.BLACKOUT and self._is_within_blackout(b.start_datetime, b.end_datetime, date, time)) or self._is_under_release(b, date, time):
                    return True
        return False

    def _is_table_blocked(self, table_id: str, date, time) -> bool:
        for b in self._active_blocks():
            if b.scope == BlockScope.TABLE and b.target_id == str(table_id):
                if (b.block_type == BlockType.BLACKOUT and self._is_within_blackout(b.start_datetime, b.end_datetime, date, time)) or self._is_under_release(b, date, time):
                    return True
        return False