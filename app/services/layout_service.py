from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.table_layout import TableLayout, RoomLayout, TableShape
from app.models.table import Table
from app.models.room import Room
from app.models.reservation import Reservation, ReservationTable
from app.schemas.layout import TableLayoutCreate, TableLayoutUpdate, RoomLayoutCreate, RoomLayoutUpdate
from datetime import date, datetime, time
from datetime import timedelta


class LayoutService:
    def __init__(self, db: Session):
        self.db = db

    def create_table_layout(self, layout_data: TableLayoutCreate) -> TableLayout:
        """Create a new table layout"""
        # Check if table exists
        table = self.db.query(Table).filter(Table.id == layout_data.table_id).first()
        if not table:
            raise ValueError("Table not found")
        
        # Check if room exists
        room = self.db.query(Room).filter(Room.id == layout_data.room_id).first()
        if not room:
            raise ValueError("Room not found")
        
        # Check if layout already exists for this table
        existing_layout = self.db.query(TableLayout).filter(
            TableLayout.table_id == layout_data.table_id
        ).first()
        
        if existing_layout:
            raise ValueError("Table layout already exists")
        
        layout = TableLayout(**layout_data.dict())
        self.db.add(layout)
        self.db.commit()
        self.db.refresh(layout)
        return layout

    def update_table_layout(self, table_id: str, layout_data: TableLayoutUpdate) -> Optional[TableLayout]:
        """Update an existing table layout"""
        layout = self.db.query(TableLayout).filter(
            TableLayout.table_id == table_id
        ).first()
        
        if not layout:
            return None
        
        update_data = layout_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(layout, field, value)
        
        self.db.commit()
        self.db.refresh(layout)
        return layout

    def get_table_layout(self, table_id: str) -> Optional[TableLayout]:
        """Get table layout by table ID"""
        return self.db.query(TableLayout).filter(
            TableLayout.table_id == table_id
        ).first()

    def get_room_layouts(self, room_id: str) -> List[TableLayout]:
        """Get all table layouts for a room"""
        return self.db.query(TableLayout).filter(
            TableLayout.room_id == room_id
        ).all()

    def delete_table_layout(self, table_id: str) -> bool:
        """Delete table layout"""
        layout = self.db.query(TableLayout).filter(
            TableLayout.table_id == table_id
        ).first()
        
        if not layout:
            return False
        
        self.db.delete(layout)
        self.db.commit()
        return True

    def create_room_layout(self, layout_data: RoomLayoutCreate) -> RoomLayout:
        """Create a new room layout"""
        # Check if room exists
        room = self.db.query(Room).filter(Room.id == layout_data.room_id).first()
        if not room:
            raise ValueError("Room not found")
        
        # Check if layout already exists for this room
        existing_layout = self.db.query(RoomLayout).filter(
            RoomLayout.room_id == layout_data.room_id
        ).first()
        
        if existing_layout:
            raise ValueError("Room layout already exists")
        
        layout = RoomLayout(**layout_data.dict())
        self.db.add(layout)
        self.db.commit()
        self.db.refresh(layout)
        return layout

    def update_room_layout(self, room_id: str, layout_data: RoomLayoutUpdate) -> Optional[RoomLayout]:
        """Update an existing room layout"""
        layout = self.db.query(RoomLayout).filter(
            RoomLayout.room_id == room_id
        ).first()
        
        if not layout:
            return None
        
        update_data = layout_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(layout, field, value)
        
        self.db.commit()
        self.db.refresh(layout)
        return layout

    def get_room_layout(self, room_id: str) -> Optional[RoomLayout]:
        """Get room layout by room ID"""
        return self.db.query(RoomLayout).filter(
            RoomLayout.room_id == room_id
        ).first()

    def get_daily_view(self, target_date: date) -> dict:
        """Get daily view with reservations and table layouts"""
        # Get all active rooms with their layouts
        rooms = self.db.query(Room).filter(Room.active == True).all()
        
        room_data = []
        for room in rooms:
            # Get room layout
            room_layout = self.get_room_layout(str(room.id))
            
            # Get tables with their layouts
            tables = self.db.query(Table).filter(
                and_(
                    Table.room_id == room.id,
                    Table.active == True
                )
            ).all()
            
            table_data = []
            for table in tables:
                table_layout = self.get_table_layout(str(table.id))
                table_data.append({
                    "id": str(table.id),
                    "name": table.name,
                    "capacity": table.capacity,
                    "room_id": str(table.room_id),
                    "room_name": room.name,
                    "active": table.active,
                    "combinable": table.combinable,
                    "layout": table_layout
                })
            
            room_data.append({
                "id": str(room.id),
                "name": room.name,
                "active": room.active,
                "layout": room_layout,
                "tables": table_data
            })
        
        # Get reservations for the date
        reservations = self.db.query(Reservation).filter(
            and_(
                Reservation.date == target_date,
                Reservation.status == "confirmed"
            )
        ).all()
        
        reservation_data = []
        for reservation in reservations:
            table_names = [table.name for table in reservation.tables] if reservation.tables else []
            
            reservation_data.append({
                "id": str(reservation.id),
                "customer_name": reservation.customer_name,
                "time": reservation.time.strftime("%H:%M"),
                "duration_hours": reservation.duration_hours_safe,
                "party_size": reservation.party_size,
                "table_names": table_names,
                "reservation_type": reservation.reservation_type.value,
                "status": reservation.status.value,
                "notes": reservation.notes,
                "admin_notes": reservation.admin_notes,
                "room_name": reservation.room.name
            })
        
        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "reservations": reservation_data,
            "rooms": room_data
        }

    def get_table_reservations(self, table_id: str, target_date: date) -> List[dict]:
        """Get all reservations for a specific table on a specific date"""
        # Get all reservations that use this table on the target date
        reservations = self.db.query(Reservation).join(
            ReservationTable
        ).filter(
            and_(
                ReservationTable.table_id == table_id,
                Reservation.date == target_date,
                Reservation.status == "confirmed"
            )
        ).all()
        
        reservation_data = []
        for reservation in reservations:
            reservation_data.append({
                "id": str(reservation.id),
                "customer_name": reservation.customer_name,
                "time": reservation.time.strftime("%H:%M"),
                "duration_hours": reservation.duration_hours_safe,
                "party_size": reservation.party_size,
                "reservation_type": reservation.reservation_type.value,
                "status": reservation.status.value,
                "notes": reservation.notes,
                "admin_notes": reservation.admin_notes
            })
        
        return reservation_data 