#!/usr/bin/env python3
"""
Comprehensive script to set up the layout system
- Creates tables for each room with proper capacity
- Assigns existing reservations to tables
- Creates room layouts and table layouts
- Fixes the daily view system
"""

import os
import sys
import psycopg2
from datetime import datetime, date
import json

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal, engine
from app.models.room import Room
from app.models.table import Table
from app.models.reservation import Reservation, ReservationTable
from app.models.table_layout import TableLayout, RoomLayout
from app.services.layout_service import LayoutService

def setup_layout_system():
    """Set up the complete layout system"""
    print("🚀 Setting up layout system...")
    
    db = SessionLocal()
    try:
        # Step 1: Get all active rooms
        rooms = db.query(Room).filter(Room.active == True).all()
        print(f"Found {len(rooms)} active rooms")
        
        for room in rooms:
            print(f"\n📋 Processing room: {room.name}")
            
            # Step 2: Create room layout if it doesn't exist
            room_layout = db.query(RoomLayout).filter(RoomLayout.room_id == room.id).first()
            if not room_layout:
                room_layout = RoomLayout(
                    room_id=room.id,
                    width=800.0,
                    height=600.0,
                    background_color="#f5f5f5"
                )
                db.add(room_layout)
                db.commit()
                print(f"  ✅ Created room layout for {room.name}")
            else:
                print(f"  ✅ Room layout already exists for {room.name}")
            
            # Step 3: Create tables for this room if they don't exist
            existing_tables = db.query(Table).filter(Table.room_id == room.id).all()
            
            if not existing_tables:
                # Create default tables based on room name
                table_configs = get_default_table_config(room.name)
                
                for i, config in enumerate(table_configs):
                    table = Table(
                        room_id=room.id,
                        name=config['name'],
                        capacity=config['capacity'],
                        combinable=config['combinable'],
                        active=True
                    )
                    db.add(table)
                    db.commit()
                    db.refresh(table)
                    
                    # Create table layout
                    table_layout = TableLayout(
                        table_id=table.id,
                        room_id=room.id,
                        x_position=config['x'],
                        y_position=config['y'],
                        width=config['width'],
                        height=config['height'],
                        shape=config['shape'],
                        color=config['color'],
                        border_color=config['border_color'],
                        text_color=config['text_color'],
                        show_capacity=True,
                        show_name=True,
                        font_size=12,
                        custom_capacity=config['capacity'],
                        z_index=i
                    )
                    db.add(table_layout)
                    print(f"  ✅ Created table {table.name} (capacity: {table.capacity})")
                
                db.commit()
            else:
                print(f"  ✅ {len(existing_tables)} tables already exist for {room.name}")
                
                # Ensure all tables have layouts
                for table in existing_tables:
                    table_layout = db.query(TableLayout).filter(TableLayout.table_id == table.id).first()
                    if not table_layout:
                        # Create default layout for existing table
                        table_layout = TableLayout(
                            table_id=table.id,
                            room_id=room.id,
                            x_position=100 + (len(existing_tables) * 150),
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
                            z_index=0
                        )
                        db.add(table_layout)
                        print(f"  ✅ Created layout for existing table {table.name}")
                
                db.commit()
            
            # Step 4: Assign existing reservations to tables
            assign_reservations_to_tables(db, room)
        
        print("\n🎉 Layout system setup complete!")
        
    except Exception as e:
        print(f"❌ Error setting up layout system: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_default_table_config(room_name):
    """Get default table configuration based on room name"""
    room_name_lower = room_name.lower()
    
    if 'front' in room_name_lower:
        # Front room - smaller tables
        return [
            {'name': 'F1', 'capacity': 2, 'combinable': True, 'x': 50, 'y': 50, 'width': 100, 'height': 60, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
            {'name': 'F2', 'capacity': 2, 'combinable': True, 'x': 170, 'y': 50, 'width': 100, 'height': 60, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
            {'name': 'F3', 'capacity': 4, 'combinable': True, 'x': 50, 'y': 130, 'width': 120, 'height': 80, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
            {'name': 'F4', 'capacity': 4, 'combinable': True, 'x': 190, 'y': 130, 'width': 120, 'height': 80, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
            {'name': 'F5', 'capacity': 6, 'combinable': True, 'x': 50, 'y': 230, 'width': 140, 'height': 100, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
        ]
    elif 'back' in room_name_lower:
        # Back room - larger tables
        return [
            {'name': 'B1', 'capacity': 4, 'combinable': True, 'x': 50, 'y': 50, 'width': 120, 'height': 80, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
            {'name': 'B2', 'capacity': 4, 'combinable': True, 'x': 190, 'y': 50, 'width': 120, 'height': 80, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
            {'name': 'B3', 'capacity': 6, 'combinable': True, 'x': 50, 'y': 150, 'width': 140, 'height': 100, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
            {'name': 'B4', 'capacity': 6, 'combinable': True, 'x': 210, 'y': 150, 'width': 140, 'height': 100, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
            {'name': 'B5', 'capacity': 8, 'combinable': True, 'x': 50, 'y': 270, 'width': 160, 'height': 120, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
        ]
    elif 'outdoor' in room_name_lower:
        # Outdoor area - mixed sizes
        return [
            {'name': 'O1', 'capacity': 2, 'combinable': True, 'x': 50, 'y': 50, 'width': 100, 'height': 60, 'shape': 'rectangular', 'color': '#e8f5e8', 'border_color': '#2d5a2d', 'text_color': '#000000'},
            {'name': 'O2', 'capacity': 2, 'combinable': True, 'x': 170, 'y': 50, 'width': 100, 'height': 60, 'shape': 'rectangular', 'color': '#e8f5e8', 'border_color': '#2d5a2d', 'text_color': '#000000'},
            {'name': 'O3', 'capacity': 4, 'combinable': True, 'x': 50, 'y': 130, 'width': 120, 'height': 80, 'shape': 'rectangular', 'color': '#e8f5e8', 'border_color': '#2d5a2d', 'text_color': '#000000'},
            {'name': 'O4', 'capacity': 4, 'combinable': True, 'x': 190, 'y': 130, 'width': 120, 'height': 80, 'shape': 'rectangular', 'color': '#e8f5e8', 'border_color': '#2d5a2d', 'text_color': '#000000'},
            {'name': 'O5', 'capacity': 6, 'combinable': True, 'x': 50, 'y': 230, 'width': 140, 'height': 100, 'shape': 'rectangular', 'color': '#e8f5e8', 'border_color': '#2d5a2d', 'text_color': '#000000'},
        ]
    else:
        # Default configuration for other rooms
        return [
            {'name': 'T1', 'capacity': 2, 'combinable': True, 'x': 50, 'y': 50, 'width': 100, 'height': 60, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
            {'name': 'T2', 'capacity': 2, 'combinable': True, 'x': 170, 'y': 50, 'width': 100, 'height': 60, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
            {'name': 'T3', 'capacity': 4, 'combinable': True, 'x': 50, 'y': 130, 'width': 120, 'height': 80, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
            {'name': 'T4', 'capacity': 4, 'combinable': True, 'x': 190, 'y': 130, 'width': 120, 'height': 80, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
            {'name': 'T5', 'capacity': 6, 'combinable': True, 'x': 50, 'y': 230, 'width': 140, 'height': 100, 'shape': 'rectangular', 'color': '#ffffff', 'border_color': '#333333', 'text_color': '#000000'},
        ]

def assign_reservations_to_tables(db, room):
    """Assign existing reservations to tables in the room"""
    print(f"  📅 Assigning reservations to tables in {room.name}")
    
    # Get all tables in this room
    tables = db.query(Table).filter(Table.room_id == room.id, Table.active == True).all()
    if not tables:
        print(f"  ⚠️  No tables found for {room.name}")
        return
    
    # Get all reservations for this room that don't have table assignments
    reservations = db.query(Reservation).filter(
        Reservation.room_id == room.id,
        Reservation.status == 'confirmed'
    ).all()
    
    assigned_count = 0
    for reservation in reservations:
        # Check if reservation already has table assignments
        existing_assignments = db.query(ReservationTable).filter(
            ReservationTable.reservation_id == reservation.id
        ).all()
        
        if existing_assignments:
            print(f"  ✅ Reservation {reservation.id} already has {len(existing_assignments)} table assignments")
            continue
        
        # Find suitable table(s) for this reservation
        suitable_tables = find_suitable_tables(db, tables, reservation)
        
        if suitable_tables:
            # Assign reservation to tables
            for table in suitable_tables:
                assignment = ReservationTable(
                    reservation_id=reservation.id,
                    table_id=table.id
                )
                db.add(assignment)
            
            assigned_count += 1
            print(f"  ✅ Assigned reservation {reservation.id} ({reservation.party_size} guests) to {len(suitable_tables)} table(s)")
        else:
            print(f"  ⚠️  No suitable tables found for reservation {reservation.id} ({reservation.party_size} guests)")
    
    db.commit()
    print(f"  📊 Assigned {assigned_count} reservations to tables in {room.name}")

def find_suitable_tables(db, tables, reservation):
    """Find suitable tables for a reservation"""
    party_size = reservation.party_size
    
    # First, try to find a single table that can accommodate the party
    for table in tables:
        if table.capacity >= party_size:
            # Check if this table is available at the reservation time
            if is_table_available(db, table, reservation):
                return [table]
    
    # If no single table works, try to combine tables
    if party_size <= 8:  # Only combine for reasonable party sizes
        # Find two tables that can be combined
        for i, table1 in enumerate(tables):
            for table2 in tables[i+1:]:
                if table1.combinable and table2.combinable:
                    combined_capacity = table1.capacity + table2.capacity
                    if combined_capacity >= party_size:
                        if is_table_available(db, table1, reservation) and is_table_available(db, table2, reservation):
                            return [table1, table2]
    
    return []

def is_table_available(db, table, reservation):
    """Check if a table is available at the reservation time"""
    # Get all reservations for this table at the same time
    conflicting_reservations = db.query(Reservation).join(ReservationTable).filter(
        ReservationTable.table_id == table.id,
        Reservation.date == reservation.date,
        Reservation.time == reservation.time,
        Reservation.status == 'confirmed'
    ).all()
    
    return len(conflicting_reservations) == 0

if __name__ == "__main__":
    print("🏗️  Layout System Setup Script")
    print("=" * 50)
    
    try:
        setup_layout_system()
        print("\n✅ Setup completed successfully!")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1) 