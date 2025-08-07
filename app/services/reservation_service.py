from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import date, datetime, timedelta
import uuid
from app.models.reservation import Reservation, ReservationStatus, ReservationTable
from app.models.room import Room, AreaType
from app.models.table import Table
from app.schemas.reservation import ReservationCreate, ReservationUpdate, ReservationWithTables
from app.services.table_service import TableService
from app.services.working_hours_service import WorkingHoursService
# from app.services.area_service import AreaService  # Temporarily disabled
from app.core.security import create_reservation_token
from app.core.config import settings


class ReservationService:
    def __init__(self, db: Session):
        self.db = db
        self.table_service = TableService(db)
        self.working_hours_service = WorkingHoursService(db)
        # self.area_service = AreaService(db)  # Temporarily disabled

    def create_reservation(self, reservation_data: ReservationCreate) -> ReservationWithTables:
        """Create a new reservation with intelligent area and table assignment"""
        # Validate business rules
        self._validate_reservation_request(reservation_data)
        
        # Determine optimal room/area for this reservation
        optimal_room_id = self._find_optimal_room_for_reservation(reservation_data)
        
        # Find best table combination in the optimal room
        table_combo = self.table_service.find_best_table_combination(
            optimal_room_id,
            reservation_data.date,
            reservation_data.time,
            reservation_data.party_size
        )
        
        if not table_combo:
            # If no tables in optimal room, try other rooms
            table_combo = self._find_tables_in_alternative_rooms(reservation_data)
            
        if not table_combo:
            raise ValueError("No suitable tables available for this reservation")
        
        # Use the room of the assigned tables
        actual_room_id = table_combo[0].room_id
        
        # Create reservation
        reservation = Reservation(
            customer_name=reservation_data.customer_name,
            email=reservation_data.email,
            phone=reservation_data.phone,
            party_size=reservation_data.party_size,
            date=reservation_data.date,
            time=reservation_data.time,
            room_id=actual_room_id,
            reservation_type=reservation_data.reservation_type,
            notes=reservation_data.notes
        )
        
        self.db.add(reservation)
        self.db.flush()  # Get the ID without committing
        
        # Assign tables
        table_ids = [str(table.id) for table in table_combo]
        self.table_service.assign_tables_to_reservation(str(reservation.id), table_ids)
        
        # Commit the transaction to persist the reservation
        self.db.commit()
        
        # Get room name for response
        room = self.db.query(Room).filter(Room.id == actual_room_id).first()
        
        # Build response with table assignments
        table_assignments = [
            {
                "table_id": str(table.id),
                "table_name": table.name,
                "capacity": table.capacity
            } for table in table_combo
        ]
        
        return ReservationWithTables(
            id=str(reservation.id),
            customer_name=reservation.customer_name,
            email=reservation.email,
            phone=reservation.phone,
            party_size=reservation.party_size,
            date=reservation.date,
            time=reservation.time,
            duration_hours=reservation.duration_hours,
            room_id=str(actual_room_id),
            room_name=room.name if room else "",
            status=reservation.status,
            reservation_type=reservation.reservation_type,
            notes=reservation.notes,
            admin_notes=reservation.admin_notes,
            created_at=reservation.created_at,
            updated_at=reservation.updated_at,
            tables=table_assignments
        )

    def get_reservation(self, reservation_id: str) -> Optional[ReservationWithTables]:
        """Get a reservation by ID with table assignments"""
        reservation = self.db.query(Reservation).filter(
            Reservation.id == reservation_id
        ).first()
        
        if not reservation:
            return None
        
        # Get room name
        room = self.db.query(Room).filter(Room.id == reservation.room_id).first()
        
        # Get table assignments
        table_assignments = []
        for rt in reservation.reservation_tables:
            table = self.db.query(Table).filter(Table.id == rt.table_id).first()
            if table:
                table_assignments.append({
                    "table_id": str(table.id),
                    "table_name": table.name,
                    "capacity": table.capacity
                })
        
        return ReservationWithTables(
            id=str(reservation.id),
            customer_name=reservation.customer_name,
            email=reservation.email,
            phone=reservation.phone,
            party_size=reservation.party_size,
            date=reservation.date,
            time=reservation.time,
            duration_hours=reservation.duration_hours_safe,
            room_id=str(reservation.room_id),
            room_name=room.name if room else "",
            status=reservation.status,
            reservation_type=reservation.reservation_type,
            notes=reservation.notes,
            admin_notes=reservation.admin_notes,
            created_at=reservation.created_at,
            updated_at=reservation.updated_at,
            tables=table_assignments
        )

    def update_reservation(self, reservation_id: str, update_data: ReservationUpdate) -> Optional[ReservationWithTables]:
        """Update a reservation"""
        reservation = self.db.query(Reservation).filter(
            Reservation.id == reservation_id
        ).first()
        
        if not reservation:
            return None
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(reservation, field, value)
        
        # If date/time/party_size changed, reassign tables
        if any(field in update_data.dict(exclude_unset=True) for field in ['date', 'time', 'party_size', 'room_id']):
            # Remove existing table assignments
            self.db.query(ReservationTable).filter(
                ReservationTable.reservation_id == reservation_id
            ).delete()
            
            # Determine optimal room/area for this reservation
            optimal_room_id = self._find_optimal_room_for_reservation(
                ReservationCreate(
                    customer_name=reservation.customer_name,
                    email=reservation.email,
                    phone=reservation.phone,
                    party_size=reservation.party_size,
                    date=reservation.date,
                    time=reservation.time,
                    reservation_type=reservation.reservation_type,
                    notes=reservation.notes
                )
            )
            
            # Find new table combination
            table_combo = self.table_service.find_best_table_combination(
                optimal_room_id,
                reservation.date,
                reservation.time,
                reservation.party_size
            )
            
            if table_combo:
                table_ids = [str(table.id) for table in table_combo]
                self.table_service.assign_tables_to_reservation(str(reservation.id), table_ids)
        
        self.db.commit()
        return self.get_reservation(str(reservation.id))

    def cancel_reservation(self, reservation_id: str) -> bool:
        """Cancel a reservation"""
        reservation = self.db.query(Reservation).filter(
            Reservation.id == reservation_id
        ).first()
        
        if not reservation:
            return False
        
        reservation.status = ReservationStatus.CANCELLED
        self.db.commit()
        return True

    def get_reservations_for_date(self, date: date, room_id: Optional[str] = None) -> List[ReservationWithTables]:
        """Get all reservations for a specific date"""
        query = self.db.query(Reservation).filter(
            and_(
                Reservation.date == date,
                Reservation.status == ReservationStatus.CONFIRMED
            )
        )
        
        if room_id:
            query = query.filter(Reservation.room_id == room_id)
        
        reservations = query.order_by(Reservation.time).all()
        
        result = []
        for reservation in reservations:
            reservation_with_tables = self.get_reservation(str(reservation.id))
            if reservation_with_tables:
                result.append(reservation_with_tables)
        
        return result

    def search_reservations(
        self, 
        customer_name: Optional[str] = None,
        email: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[ReservationWithTables]:
        """Search reservations by various criteria"""
        query = self.db.query(Reservation)
        
        if customer_name:
            query = query.filter(Reservation.customer_name.ilike(f"%{customer_name}%"))
        
        if email:
            query = query.filter(Reservation.email.ilike(f"%{email}%"))
        
        if date_from:
            query = query.filter(Reservation.date >= date_from)
        
        if date_to:
            query = query.filter(Reservation.date <= date_to)
        
        reservations = query.order_by(desc(Reservation.created_at)).all()
        
        result = []
        for reservation in reservations:
            reservation_with_tables = self.get_reservation(str(reservation.id))
            if reservation_with_tables:
                result.append(reservation_with_tables)
        
        return result

    def _validate_reservation_request(self, reservation_data: ReservationCreate):
        """Validate reservation request against business rules"""
        print(f"DEBUG: Starting validation for reservation")
        print(f"DEBUG: Party size: {reservation_data.party_size}")
        print(f"DEBUG: Date: {reservation_data.date}")
        print(f"DEBUG: Time: {reservation_data.time}")
        print(f"DEBUG: Time type: {type(reservation_data.time)}")
        
        # Check party size limits
        if reservation_data.party_size > settings.MAX_PARTY_SIZE:
            raise ValueError(f"Party size cannot exceed {settings.MAX_PARTY_SIZE} people")
        
        if reservation_data.party_size < 1:
            raise ValueError("Party size must be at least 1")
        
        # Validate working hours
        is_valid_time, error_message = self.working_hours_service.validate_reservation_time(
            reservation_data.date, reservation_data.time
        )
        
        if not is_valid_time:
            raise ValueError(error_message)
        
        # Check if room exists and is active (only if room_id is specified)
        if reservation_data.room_id:
            print(f"DEBUG: Checking room {reservation_data.room_id}")
            room = self.db.query(Room).filter(
                and_(
                    Room.id == reservation_data.room_id,
                    Room.active == True
                )
            ).first()
            
            if not room:
                raise ValueError("Invalid or inactive room")
        
        print("DEBUG: Validation completed successfully") 

    def _find_optimal_room_for_reservation(self, reservation_data: ReservationCreate) -> Optional[str]:
        """Find the optimal room for a reservation based on reservation type and party size"""
        
        # Simple fallback: if room_id specified, use it; otherwise find any active room
        if reservation_data.room_id:
            return reservation_data.room_id
        
        # Find any active room with sufficient capacity
        rooms = self.db.query(Room).filter(Room.active == True).all()
        
        for room in rooms:
            # Check if this room has tables with sufficient capacity
            total_capacity = self.table_service._get_room_capacity(room.id)
            if total_capacity >= reservation_data.party_size:
                return room.id
        
        # Return first active room as fallback
        if rooms:
            return rooms[0].id
            
        return None

    def _determine_preferred_area_type(self, reservation_type: str) -> Optional[str]:
        """Determine preferred area type based on reservation type"""
        
        # Simplified without AreaType enum - just return None for now
        return None

    def _find_fallback_room(self, party_size: int, preferred_area_type: Optional[str]) -> Optional[str]:
        """Find a fallback room when optimal room is not available"""
        
        # Get all active rooms (area_type and priority columns are disabled)
        rooms = self.db.query(Room).filter(Room.active == True).all()
        
        # Check each room for capacity
        for room in rooms:
            total_capacity = self._get_room_capacity(room.id)
            if total_capacity >= party_size:
                return room.id
        
        return None

    def _get_room_capacity(self, room_id: str) -> int:
        """Get total capacity of all active tables in a room"""
        tables = self.db.query(Table).filter(
            and_(
                Table.room_id == room_id,
                Table.active == True
            )
        ).all()
        return sum(table.capacity for table in tables)

    def _find_tables_in_alternative_rooms(self, reservation_data: ReservationCreate) -> Optional[List[Table]]:
        """Find tables in alternative rooms when preferred room is full"""
        
        # Get all active rooms (priority column is disabled)
        rooms = self.db.query(Room).filter(Room.active == True).all()
        
        # Try each room for table availability
        for room in rooms:
            table_combo = self.table_service.find_best_table_combination(
                room.id,
                reservation_data.date,
                reservation_data.time,
                reservation_data.party_size
            )
            if table_combo:
                return table_combo
        
        return None

    def get_smart_availability(
        self, 
        date: date, 
        party_size: int, 
        preferred_area_type: Optional[str] = None,
        reservation_type: str = "dinner"
    ) -> Dict[str, Any]:
        """Get smart availability with area recommendations"""
        
        optimal_area_type = self._determine_preferred_area_type(reservation_type)
        
        # Get all active rooms (priority column is disabled)
        rooms = self.db.query(Room).filter(Room.active == True).all()
        
        availability_data = {
            "date": date.isoformat(),
            "recommended_area_type": optimal_area_type.value if optimal_area_type else None,
            "reservation_type": reservation_type,
            "rooms": []
        }
        
        for room in rooms:
            room_availability = self._get_room_availability(room, date, party_size)
            if room_availability:
                availability_data["rooms"].append(room_availability)
        
        return availability_data

    def _get_room_availability(self, room: Room, date: date, party_size: int) -> Optional[Dict[str, Any]]:
        """Get availability for a specific room"""
        
        # Get available time slots for this room
        time_slots = self.table_service.get_availability_for_date(
            room.id, date, party_size
        )
        
        if not time_slots:
            return None
        
        return {
            "room_id": str(room.id),
            "room_name": room.name,
            "area_type": "indoor",  # Default since area_type column is disabled
            "priority": 5,  # Default since priority column is disabled
            "is_fallback_area": False,  # Default since column is disabled
            "fallback_for": None,  # Default since column is disabled
            "total_capacity": self._get_room_capacity(room.id),
            "available_time_slots": [
                {
                    "time": slot.time.strftime("%H:%M"),
                    "total_capacity": slot.total_capacity,
                    "table_count": len(slot.available_tables)
                } for slot in time_slots
            ]
        } 