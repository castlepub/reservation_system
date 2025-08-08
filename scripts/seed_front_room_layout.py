#!/usr/bin/env python3
"""
Seed or update the Front Room tables and layout to match the current real-world setup.

This script is idempotent: running it multiple times will keep names stable,
update capacities/combinable flags, and upsert the corresponding TableLayout
records (positions, sizes, shapes).

Usage:
  python scripts/seed_front_room_layout.py
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.room import Room
from app.models.table import Table
from app.models.table_layout import TableLayout, RoomLayout, TableShape


FRONT_ROOM_NAME = "Front Room"


def front_room_config():
    """Return the canonical Front Room table definitions with layout."""
    return [
        # name, capacity, combinable, shape, x, y, width, height
        {"name": "01", "capacity": 2, "combinable": True,  "shape": TableShape.SQUARE.value,       "x": 40,  "y": 20,  "width": 60,  "height": 60},
        {"name": "02", "capacity": 3, "combinable": True,  "shape": TableShape.SQUARE.value,       "x": 40,  "y": 110, "width": 60,  "height": 60},
        {"name": "03", "capacity": 4, "combinable": True,  "shape": TableShape.SQUARE.value,       "x": 40,  "y": 200, "width": 60,  "height": 70},
        {"name": "05", "capacity": 6, "combinable": True,  "shape": TableShape.RECTANGULAR.value,  "x": 60,  "y": 300, "width": 80,  "height": 110},
        {"name": "06", "capacity": 5, "combinable": True,  "shape": TableShape.RECTANGULAR.value,  "x": 60,  "y": 420, "width": 80,  "height": 100},
        {"name": "BAR", "capacity": 0, "combinable": False, "shape": TableShape.RECTANGULAR.value,  "x": 580, "y": 180, "width": 380, "height": 200},
        {"name": "Carsten", "capacity": 6, "combinable": True, "shape": TableShape.RECTANGULAR.value, "x": 220, "y": 500, "width": 220, "height": 80},
        {"name": "Entrance 2", "capacity": 3, "combinable": True, "shape": TableShape.RECTANGULAR.value, "x": 440, "y": 20,  "width": 80,  "height": 60},
        {"name": "Green wall", "capacity": 2, "combinable": True, "shape": TableShape.RECTANGULAR.value, "x": 830, "y": 30,  "width": 90,  "height": 140},
        {"name": "high tab1", "capacity": 12, "combinable": False, "shape": TableShape.RECTANGULAR.value, "x": 480, "y": 420, "width": 80,  "height": 180},
        {"name": "High Tab2", "capacity": 2, "combinable": True, "shape": TableShape.SQUARE.value,       "x": 700, "y": 500, "width": 70,  "height": 70},
        {"name": "High Tab3", "capacity": 3, "combinable": True, "shape": TableShape.SQUARE.value,       "x": 840, "y": 520, "width": 70,  "height": 70},
        {"name": "Politi-x", "capacity": 3, "combinable": True, "shape": TableShape.SQUARE.value,       "x": 680, "y": 20,  "width": 70,  "height": 60},
        {"name": "Ray 04", "capacity": 4, "combinable": True,  "shape": TableShape.ROUND.value,         "x": 320, "y": 210, "width": 70,  "height": 70},
    ]


def upsert_front_room(db):
    # Ensure room exists
    room = db.query(Room).filter(Room.name == FRONT_ROOM_NAME).first()
    if not room:
        room = Room(name=FRONT_ROOM_NAME, description="Front dining area")
        db.add(room)
        db.commit()
        db.refresh(room)

    # Ensure room layout exists
    room_layout = db.query(RoomLayout).filter(RoomLayout.room_id == room.id).first()
    if not room_layout:
        room_layout = RoomLayout(
            room_id=room.id,
            width=950.0,
            height=620.0,
            background_color="#f5f5f5",
        )
        db.add(room_layout)
        db.commit()

    # Upsert tables & layouts
    for cfg in front_room_config():
        table = (
            db.query(Table)
            .filter(Table.room_id == room.id, Table.name == cfg["name"]) 
            .first()
        )
        if not table:
            table = Table(
                room_id=room.id,
                name=cfg["name"],
                capacity=cfg["capacity"],
                combinable=cfg["combinable"],
                public_bookable=True,
                active=True,
            )
            db.add(table)
            db.commit()
            db.refresh(table)
        else:
            # Update core attributes
            table.capacity = cfg["capacity"]
            table.combinable = cfg["combinable"]
            table.active = True
            db.commit()

        layout = db.query(TableLayout).filter(TableLayout.table_id == table.id).first()
        if not layout:
            layout = TableLayout(
                table_id=table.id,
                room_id=room.id,
                x_position=cfg["x"],
                y_position=cfg["y"],
                width=cfg["width"],
                height=cfg["height"],
                shape=cfg["shape"],
                color="#ffffff",
                border_color="#333333",
                text_color="#000000",
                show_capacity=True,
                show_name=True,
                font_size=12,
                custom_capacity=cfg["capacity"],
                z_index=1,
            )
            db.add(layout)
        else:
            layout.x_position = cfg["x"]
            layout.y_position = cfg["y"]
            layout.width = cfg["width"]
            layout.height = cfg["height"]
            layout.shape = cfg["shape"]
            layout.custom_capacity = cfg["capacity"]
        db.commit()

    print("✓ Front Room tables and layout seeded/updated")


def main():
    db = SessionLocal()
    try:
        upsert_front_room(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()


