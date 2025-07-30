from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import date, time
import itertools
from app.models.table import Table
from app.models.reservation import Reservation, ReservationTable
from app.schemas.reservation import TableAssignment, TimeSlot


class TableService:
    def __init__(self, db: Session):
        self.db = db

    def get_available_tables(
        self, 
        room_id: str, 
        date: date, 
        time: time,
        party_size: int
    ) -> List[Table]:
        """Get all available tables for a given room, date, and time"""
        # Get all active tables in the room
        tables = self.db.query(Table).filter(
            and_(
                Table.room_id == room_id,
                Table.active == True
            )
        ).all()

        # Get tables that are already reserved for this time
        reserved_tables = self.db.query(ReservationTable.table_id).join(
            Reservation
        ).filter(
            and_(
                Reservation.date == date,
                Reservation.time == time,
                Reservation.status == "confirmed"
            )
        ).all()
        
        reserved_table_ids = [rt.table_id for rt in reserved_tables]
        
        # Filter out reserved tables
        available_tables = [t for t in tables if t.id not in reserved_table_ids]
        
        return available_tables

    def get_available_tables_all_rooms(
        self, 
        date: date, 
        time: time,
        party_size: int
    ) -> List[Table]:
        """Get all available tables across all active rooms for a given date and time"""
        # Get all active tables from all active rooms
        from app.models.room import Room
        tables = self.db.query(Table).join(Room).filter(
            and_(
                Table.active == True,
                Room.active == True
            )
        ).all()

        # Get tables that are already reserved for this time
        reserved_tables = self.db.query(ReservationTable.table_id).join(
            Reservation
        ).filter(
            and_(
                Reservation.date == date,
                Reservation.time == time,
                Reservation.status == "confirmed"
            )
        ).all()
        
        reserved_table_ids = [rt.table_id for rt in reserved_tables]
        
        # Filter out reserved tables
        available_tables = [t for t in tables if t.id not in reserved_table_ids]
        
        return available_tables

    def find_best_table_combination(
        self, 
        room_id: Optional[str], 
        date: date, 
        time: time,
        party_size: int
    ) -> Optional[List[Table]]:
        """
        Find the best combination of tables for a party size.
        If room_id is None, searches across all active rooms.
        Returns the combination with smallest excess seats and fewest tables.
        """
        if room_id:
            # Search in specific room
            available_tables = self.get_available_tables(room_id, date, time, party_size)
        else:
            # Search across all active rooms
            available_tables = self.get_available_tables_all_rooms(date, time, party_size)
        
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

        # Try combinations within each room
        for room_id, room_tables in tables_by_room.items():
            # Try combinations of 2 to 4 tables (reasonable limit) within the same room
            for r in range(2, min(5, len(room_tables) + 1)):
                for combo in itertools.combinations(room_tables, r):
                    total_capacity = sum(table.capacity for table in combo)
                    
                    if total_capacity >= party_size:
                        # Score: excess seats + number of tables (weighted)
                        excess_seats = total_capacity - party_size
                        num_tables = len(combo)
                        score = excess_seats + (num_tables * 0.1)  # Small penalty for more tables
                        
                        if score < best_score:
                            best_score = score
                            best_combination = list(combo)

        return best_combination

    def get_availability_for_date(
        self, 
        room_id: str, 
        date: date, 
        party_size: int
    ) -> List[TimeSlot]:
        """Get available time slots for a given date and party size"""
        from app.core.config import settings
        
        time_slots = []
        
        # Generate time slots from opening to closing hour
        for hour in range(settings.OPENING_HOUR, settings.CLOSING_HOUR):
            for minute in [0, 30]:  # 30-minute intervals
                time_slot = time(hour, minute)
                
                # Check if tables are available for this time
                available_tables = self.get_available_tables(room_id, date, time_slot, party_size)
                
                if available_tables:
                    # Find best combination
                    best_combo = self.find_best_table_combination(room_id, date, time_slot, party_size)
                    
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