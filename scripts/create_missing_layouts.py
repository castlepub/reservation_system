#!/usr/bin/env python3
"""
Script to create missing table_layouts records for existing tables
"""
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.table import Table
from app.models.table_layout import TableLayout
import uuid

def create_missing_layouts():
    """Create table_layouts for tables that don't have them"""
    db = next(get_db())
    
    try:
        # Get all tables
        tables = db.query(Table).all()
        print(f"Found {len(tables)} tables")
        
        # Get existing layout table_ids
        existing_layouts = db.query(TableLayout.table_id).all()
        existing_table_ids = {layout[0] for layout in existing_layouts}
        print(f"Found {len(existing_table_ids)} existing layouts")
        
        created_count = 0
        for table in tables:
            if table.id not in existing_table_ids:
                print(f"Creating layout for table {table.name} (ID: {table.id})")
                
                # Calculate position based on table index for a grid layout
                tables_in_room = db.query(Table).filter(Table.room_id == table.room_id).all()
                table_index = [t.id for t in tables_in_room].index(table.id)
                
                # Grid positioning (4 tables per row)
                row = table_index // 4
                col = table_index % 4
                x_pos = 50 + (col * 120)
                y_pos = 50 + (row * 100)
                
                # Create layout record
                layout = TableLayout(
                    id=str(uuid.uuid4()),
                    table_id=table.id,
                    room_id=table.room_id,
                    x_position=float(x_pos),
                    y_position=float(y_pos),
                    width=100.0,
                    height=80.0,
                    shape="rectangular",
                    color="#4CAF50",
                    border_color="#2E7D32",
                    text_color="#FFFFFF",
                    show_capacity=True,
                    show_name=True,
                    font_size=12,
                    custom_capacity=table.capacity,
                    is_connected=False,
                    z_index=1
                )
                
                db.add(layout)
                created_count += 1
        
        if created_count > 0:
            db.commit()
            print(f"✅ Created {created_count} missing table layouts")
        else:
            print("✅ All tables already have layouts")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_missing_layouts()