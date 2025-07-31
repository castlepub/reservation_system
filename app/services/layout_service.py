from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from app.models.table_layout import TableLayout, RoomLayout, TableShape
from app.models.table import Table
from app.models.room import Room
from app.models.reservation import Reservation
from app.schemas.layout import (
    TableLayoutCreate, TableLayoutUpdate, TableLayoutResponse,
    RoomLayoutCreate, RoomLayoutUpdate, RoomLayoutResponse,
    LayoutEditorData, TableWithReservation
)
from datetime import datetime, date
import json


class LayoutService:
    def __init__(self, db: Session):
        self.db = db

    # Table Layout Management
    def create_table_layout(self, layout_data: TableLayoutCreate) -> TableLayout:
        """Create a new table layout"""
        layout = TableLayout(
            table_id=layout_data.table_id,
            room_id=layout_data.room_id,
            x_position=layout_data.x_position,
            y_position=layout_data.y_position,
            width=layout_data.width,
            height=layout_data.height,
            shape=layout_data.shape,
            color=layout_data.color,
            border_color=layout_data.border_color,
            text_color=layout_data.text_color,
            show_capacity=layout_data.show_capacity,
            show_name=layout_data.show_name,
            font_size=layout_data.font_size,
            custom_capacity=layout_data.custom_capacity,
            is_connected=layout_data.is_connected,
            connected_to=layout_data.connected_to,
            z_index=layout_data.z_index
        )
        self.db.add(layout)
        self.db.commit()
        self.db.refresh(layout)
        return layout

    def update_table_layout(self, layout_id: str, layout_data: TableLayoutUpdate) -> Optional[TableLayout]:
        """Update an existing table layout"""
        layout = self.db.query(TableLayout).filter(TableLayout.id == layout_id).first()
        if not layout:
            return None
        
        for field, value in layout_data.dict(exclude_unset=True).items():
            setattr(layout, field, value)
        
        layout.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(layout)
        return layout

    def delete_table_layout(self, layout_id: str) -> bool:
        """Delete a table layout"""
        layout = self.db.query(TableLayout).filter(TableLayout.id == layout_id).first()
        if not layout:
            return False
        
        self.db.delete(layout)
        self.db.commit()
        return True

    def get_table_layout(self, layout_id: str) -> Optional[TableLayout]:
        """Get a specific table layout"""
        return self.db.query(TableLayout).filter(TableLayout.id == layout_id).first()

    def get_table_layouts_by_room(self, room_id: str) -> List[TableLayout]:
        """Get all table layouts for a specific room"""
        return self.db.query(TableLayout).filter(TableLayout.room_id == room_id).all()

    # Room Layout Management
    def create_room_layout(self, layout_data: RoomLayoutCreate) -> RoomLayout:
        """Create a new room layout"""
        layout = RoomLayout(
            room_id=layout_data.room_id,
            width=layout_data.width,
            height=layout_data.height,
            background_color=layout_data.background_color,
            grid_enabled=layout_data.grid_enabled,
            grid_size=layout_data.grid_size,
            grid_color=layout_data.grid_color,
            show_entrance=layout_data.show_entrance,
            entrance_position=layout_data.entrance_position,
            show_bar=layout_data.show_bar,
            bar_position=layout_data.bar_position
        )
        self.db.add(layout)
        self.db.commit()
        self.db.refresh(layout)
        return layout

    def update_room_layout(self, room_id: str, layout_data: RoomLayoutUpdate) -> Optional[RoomLayout]:
        """Update an existing room layout"""
        layout = self.db.query(RoomLayout).filter(RoomLayout.room_id == room_id).first()
        if not layout:
            return None
        
        for field, value in layout_data.dict(exclude_unset=True).items():
            setattr(layout, field, value)
        
        layout.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(layout)
        return layout

    def get_room_layout(self, room_id: str) -> Optional[RoomLayout]:
        """Get room layout for a specific room"""
        return self.db.query(RoomLayout).filter(RoomLayout.room_id == room_id).first()

    # Layout Editor Data
    def get_layout_editor_data(self, room_id: str, target_date: date) -> LayoutEditorData:
        """Get comprehensive data for the layout editor"""
        # Get room layout
        room_layout = self.get_room_layout(room_id)
        if not room_layout:
            # Create default room layout
            room_layout = self.create_room_layout(RoomLayoutCreate(
                room_id=room_id,
                width=800.0,
                height=600.0
            ))

        # Get table layouts with table data
        table_layouts = self.db.query(TableLayout, Table).join(Table).filter(
            TableLayout.room_id == room_id
        ).all()

        # Get reservations for the target date
        reservations = self.db.query(Reservation).filter(
            Reservation.date == target_date
        ).all()

        # Create table with reservation data
        tables_with_reservations = []
        for layout, table in table_layouts:
            # Find reservations for this table
            table_reservations = [
                r for r in reservations 
                if table.name in (r.assigned_tables or [])
            ]
            
            table_with_reservation = TableWithReservation(
                layout_id=layout.id,
                table_id=table.id,
                table_name=table.name,
                capacity=layout.custom_capacity or table.capacity,
                x_position=layout.x_position,
                y_position=layout.y_position,
                width=layout.width,
                height=layout.height,
                shape=layout.shape,
                color=layout.color,
                border_color=layout.border_color,
                text_color=layout.text_color,
                show_capacity=layout.show_capacity,
                show_name=layout.show_name,
                font_size=layout.font_size,
                is_connected=layout.is_connected,
                connected_to=layout.connected_to,
                z_index=layout.z_index,
                reservations=table_reservations
            )
            tables_with_reservations.append(table_with_reservation)

        return LayoutEditorData(
            room_id=room_id,
            room_layout=room_layout,
            tables=tables_with_reservations,
            reservations=reservations
        )

    # Smart Table Assignment
    def suggest_table_assignment(self, room_id: str, party_size: int, target_date: date, target_time: str) -> List[Dict[str, Any]]:
        """Suggest optimal table assignments for a reservation"""
        # Get available tables for the room
        table_layouts = self.get_table_layouts_by_room(room_id)
        
        # Get existing reservations for the time slot
        existing_reservations = self.db.query(Reservation).filter(
            and_(
                Reservation.date == target_date,
                Reservation.time == target_time
            )
        ).all()
        
        # Get reserved table names
        reserved_tables = set()
        for reservation in existing_reservations:
            if reservation.assigned_tables:
                reserved_tables.update(reservation.assigned_tables)
        
        suggestions = []
        for layout in table_layouts:
            table = layout.table
            if table.name in reserved_tables:
                continue
            
            # Check if table capacity matches party size
            capacity = layout.custom_capacity or table.capacity
            if capacity >= party_size:
                suggestions.append({
                    "table_id": table.id,
                    "table_name": table.name,
                    "layout_id": layout.id,
                    "capacity": capacity,
                    "x_position": layout.x_position,
                    "y_position": layout.y_position,
                    "shape": layout.shape,
                    "score": capacity - party_size  # Lower score is better (closer fit)
                })
        
        # Sort by score (best fit first)
        suggestions.sort(key=lambda x: x["score"])
        return suggestions[:5]  # Return top 5 suggestions

    # Export/Import
    def export_room_layout(self, room_id: str) -> Dict[str, Any]:
        """Export room layout as JSON"""
        room_layout = self.get_room_layout(room_id)
        table_layouts = self.get_table_layouts_by_room(room_id)
        
        return {
            "room_id": room_id,
            "exported_at": datetime.utcnow().isoformat(),
            "room_layout": {
                "width": room_layout.width,
                "height": room_layout.height,
                "background_color": room_layout.background_color,
                "grid_enabled": room_layout.grid_enabled,
                "grid_size": room_layout.grid_size,
                "grid_color": room_layout.grid_color,
                "show_entrance": room_layout.show_entrance,
                "entrance_position": room_layout.entrance_position,
                "show_bar": room_layout.show_bar,
                "bar_position": room_layout.bar_position
            },
            "table_layouts": [
                {
                    "table_id": layout.table_id,
                    "x_position": layout.x_position,
                    "y_position": layout.y_position,
                    "width": layout.width,
                    "height": layout.height,
                    "shape": layout.shape.value,
                    "color": layout.color,
                    "border_color": layout.border_color,
                    "text_color": layout.text_color,
                    "show_capacity": layout.show_capacity,
                    "show_name": layout.show_name,
                    "font_size": layout.font_size,
                    "custom_capacity": layout.custom_capacity,
                    "is_connected": layout.is_connected,
                    "connected_to": layout.connected_to,
                    "z_index": layout.z_index
                }
                for layout in table_layouts
            ]
        }

    def import_room_layout(self, room_id: str, layout_data: Dict[str, Any]) -> bool:
        """Import room layout from JSON"""
        try:
            # Update room layout
            room_layout_data = layout_data.get("room_layout", {})
            self.update_room_layout(room_id, RoomLayoutUpdate(**room_layout_data))
            
            # Clear existing table layouts
            existing_layouts = self.get_table_layouts_by_room(room_id)
            for layout in existing_layouts:
                self.db.delete(layout)
            
            # Create new table layouts
            for table_layout_data in layout_data.get("table_layouts", []):
                self.create_table_layout(TableLayoutCreate(
                    table_id=table_layout_data["table_id"],
                    room_id=room_id,
                    **{k: v for k, v in table_layout_data.items() if k != "table_id"}
                ))
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e 