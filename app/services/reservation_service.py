from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import date, datetime, timedelta
import uuid
from app.models.reservation import Reservation, ReservationStatus, ReservationTable
from app.models.room import Room
from app.models.table import Table
from app.schemas.reservation import ReservationCreate, ReservationUpdate, ReservationWithTables
from app.services.table_service import TableService
from app.core.security import create_reservation_token
from app.core.config import settings


class ReservationService:
    def __init__(self, db: Session):
        self.db = db
        self.table_service = TableService(db)

    def create_reservation(self, reservation_data: ReservationCreate) -> ReservationWithTables:
        """Create a new reservation with automatic table assignment"""
        # Validate business rules
        self._validate_reservation_request(reservation_data)
        
        # Find best table combination
        table_combo = self.table_service.find_best_table_combination(
            reservation_data.room_id,
            reservation_data.date,
            reservation_data.time,
            reservation_data.party_size
        )
        
        if not table_combo:
            raise ValueError("No suitable tables available for this reservation")
        
        # Create reservation
        reservation = Reservation(
            customer_name=reservation_data.customer_name,
            email=reservation_data.email,
            phone=reservation_data.phone,
            party_size=reservation_data.party_size,
            date=reservation_data.date,
            time=reservation_data.time,
            room_id=reservation_data.room_id,
            notes=reservation_data.notes
        )
        
        self.db.add(reservation)
        self.db.flush()  # Get the ID without committing
        
        # Assign tables
        table_ids = [str(table.id) for table in table_combo]
        self.table_service.assign_tables_to_reservation(str(reservation.id), table_ids)
        
        # Get room name for response
        room = self.db.query(Room).filter(Room.id == reservation.room_id).first()
        
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
            room_id=str(reservation.room_id),
            room_name=room.name if room else "",
            status=reservation.status,
            notes=reservation.notes,
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
            room_id=str(reservation.room_id),
            room_name=room.name if room else "",
            status=reservation.status,
            notes=reservation.notes,
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
            
            # Find new table combination
            table_combo = self.table_service.find_best_table_combination(
                reservation.room_id,
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
        # Check party size limits
        if reservation_data.party_size > settings.MAX_PARTY_SIZE:
            raise ValueError(f"Party size cannot exceed {settings.MAX_PARTY_SIZE} people")
        
        if reservation_data.party_size < 1:
            raise ValueError("Party size must be at least 1")
        
        # Check reservation time limits
        reservation_datetime = datetime.combine(reservation_data.date, reservation_data.time)
        now = datetime.now()
        
        # Minimum hours in advance
        min_datetime = now + timedelta(hours=settings.MIN_RESERVATION_HOURS)
        if reservation_datetime < min_datetime:
            raise ValueError(f"Reservations must be made at least {settings.MIN_RESERVATION_HOURS} hours in advance")
        
        # Maximum days in advance
        max_datetime = now + timedelta(days=settings.MAX_RESERVATION_DAYS)
        if reservation_datetime > max_datetime:
            raise ValueError(f"Reservations cannot be made more than {settings.MAX_RESERVATION_DAYS} days in advance")
        
        # Check operating hours
        if reservation_data.time.hour < settings.OPENING_HOUR or reservation_data.time.hour >= settings.CLOSING_HOUR:
            raise ValueError(f"Reservations are only accepted between {settings.OPENING_HOUR}:00 and {settings.CLOSING_HOUR}:00")
        
        # Check if room exists and is active
        room = self.db.query(Room).filter(
            and_(
                Room.id == reservation_data.room_id,
                Room.active == True
            )
        ).first()
        
        if not room:
            raise ValueError("Invalid or inactive room") 