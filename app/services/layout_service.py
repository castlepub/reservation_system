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
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = 300  # 5 minutes TTL

    # Table Layout Management
    def create_table_layout(self, layout_data: TableLayoutCreate) -> TableLayout:
        """Create a new table layout. If table_id is not provided, create a Table first."""
        # If table_id is missing, create a new Table record using provided optional fields
        table_id = layout_data.table_id
        if not table_id:
            # Validate required info for creating a Table
            if not layout_data.table_name or layout_data.capacity is None:
                raise ValueError("Either table_id must be provided or table_name and capacity must be supplied to create a new table.")

            new_table = Table(
                room_id=layout_data.room_id,
                name=layout_data.table_name,
                capacity=layout_data.capacity,
                combinable=layout_data.combinable if layout_data.combinable is not None else True,
            )
            self.db.add(new_table)
            self.db.flush()  # obtain new_table.id without committing yet
            table_id = new_table.id

        layout = TableLayout(
            table_id=table_id,
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

        # Clear cache for this room
        self._clear_room_cache(layout_data.room_id)

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
        
        # Clear cache for this room
        self._clear_room_cache(layout.room_id)
        
        return layout

    def delete_table_layout(self, layout_id: str) -> bool:
        """Delete a table layout"""
        layout = self.db.query(TableLayout).filter(TableLayout.id == layout_id).first()
        if not layout:
            return False
        
        room_id = layout.room_id
        self.db.delete(layout)
        self.db.commit()
        
        # Clear cache for this room
        self._clear_room_cache(room_id)
        
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
    def _get_cache_key(self, room_id: str, target_date: date) -> str:
        """Generate cache key for layout data"""
        return f"layout_editor_{room_id}_{target_date}"
    
    def _get_from_cache(self, key: str):
        """Get data from cache if not expired"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.utcnow() - timestamp).seconds < self._cache_ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data):
        """Set data in cache with timestamp"""
        self._cache[key] = (data, datetime.utcnow())
    
    def _clear_room_cache(self, room_id: str):
        """Clear cache for a specific room"""
        keys_to_remove = [key for key in self._cache.keys() if f"layout_editor_{room_id}_" in key]
        for key in keys_to_remove:
            del self._cache[key]
    
    def get_layout_editor_data(self, room_id: str, target_date: date) -> LayoutEditorData:
        """Get comprehensive data for the layout editor"""
        # Check cache first
        cache_key = self._get_cache_key(room_id, target_date)
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Get room layout
        room_layout = self.get_room_layout(room_id)
        if not room_layout:
            # Create default room layout
            room_layout = self.create_room_layout(RoomLayoutCreate(
                room_id=room_id,
                width=800.0,
                height=600.0
            ))

        # Get all tables for this room
        tables = self.db.query(Table).filter(
            Table.room_id == room_id,
            Table.active == True
        ).all()

        # Ensure each table has a layout; create defaults for missing ones in a grid
        existing_layouts = self.db.query(TableLayout).filter(TableLayout.room_id == room_id).all()
        layouts_by_table_id = {l.table_id: l for l in existing_layouts}
        if tables:
            default_width = 100.0
            default_height = 80.0
            spacing_x = 30.0
            spacing_y = 30.0
            columns = 8
            index = 0
            # continue after existing layouts count for consistent positioning
            start_index = len(existing_layouts)
            for table in tables:
                if table.id not in layouts_by_table_id:
                    total_index = start_index + index
                    col = total_index % columns
                    row = total_index // columns
                    x_pos = 25 + col * (default_width + spacing_x)
                    y_pos = 25 + row * (default_height + spacing_y)
                    layout = TableLayout(
                        table_id=str(table.id),
                        room_id=room_id,
                        x_position=x_pos,
                        y_position=y_pos,
                        width=default_width,
                        height=default_height,
                        shape=TableShape.RECTANGULAR,
                        color="#4A90E2",
                        border_color="#2E5BBA",
                        text_color="#FFFFFF",
                        show_capacity=True,
                        show_name=True,
                        font_size=12,
                        custom_capacity=None,
                        is_connected=False,
                        connected_to=None,
                        z_index=1,
                    )
                    self.db.add(layout)
                    index += 1
            if index > 0:
                self.db.commit()

        # Get table layouts with table data (now guaranteed to exist for all tables)
        table_layouts = self.db.query(TableLayout, Table).join(Table).filter(
            TableLayout.room_id == room_id
        ).all()

        # Create a map of table_id to layout
        layout_map = {table.id: layout for layout, table in table_layouts}
        
        # Get table names for this room to filter reservations efficiently
        room_table_names = [table.name for table in tables]
        
        # Get reservations for the target date that are assigned to tables in this room
        from app.models.reservation import ReservationTable
        
        # Get table IDs for this room
        room_table_ids = [table.id for table in tables]
        
        # Get reservations that have table assignments in this room
        reservations = []
        if room_table_ids:
            reservation_ids = self.db.query(ReservationTable.reservation_id).filter(
                ReservationTable.table_id.in_(room_table_ids)
            ).distinct().all()
            
            if reservation_ids:
                reservation_ids = [r[0] for r in reservation_ids]
                reservations = self.db.query(Reservation).filter(
                    and_(
                        Reservation.date == target_date,
                        Reservation.id.in_(reservation_ids)
                    )
                ).all()

        # Create table with reservation data
        tables_with_reservations = []
        for table in tables:
            # Get or create layout for this table
            layout = layout_map.get(table.id)
            if not layout:
                # Create default layout for this table
                layout = self.create_table_layout(TableLayoutCreate(
                    table_id=table.id,
                    room_id=room_id,
                    x_position=100 + (len(tables_with_reservations) * 150),
                    y_position=100,
                    width=120,
                    height=80,
                    shape="rectangular",
                    color="#ffffff",
                    border_color="#333333",
                    text_color="#000000",
                    show_capacity=True,
                    show_name=True,
                    font_size=12,
                    custom_capacity=table.capacity,
                    z_index=len(tables_with_reservations)
                ))
            
            # Find reservations for this table
            table_reservations = []
            for reservation in reservations:
                # Check if this reservation is assigned to this table
                table_assignment = self.db.query(ReservationTable).filter(
                    and_(
                        ReservationTable.reservation_id == reservation.id,
                        ReservationTable.table_id == table.id
                    )
                ).first()
                if table_assignment:
                    table_reservations.append(reservation)
            
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

        result = LayoutEditorData(
            room_id=room_id,
            room_layout=room_layout,
            tables=tables_with_reservations,
            reservations=reservations
        )
        
        # Cache the result
        self._set_cache(cache_key, result)
        
        return result

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
            # Get table assignments for this reservation
            table_assignments = self.db.query(ReservationTable).filter(
                ReservationTable.reservation_id == reservation.id
            ).all()
            for assignment in table_assignments:
                table = self.db.query(Table).filter(Table.id == assignment.table_id).first()
                if table:
                    reserved_tables.add(table.name)
        
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