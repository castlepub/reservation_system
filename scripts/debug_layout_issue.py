#!/usr/bin/env python3
"""
Script to debug the layout issue by checking specific table IDs
"""
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.table_layout import TableLayout
from app.models.table import Table

def debug_layout_issue():
    """Debug the layout issue"""
    db = next(get_db())
    
    try:
        # Check the specific table IDs from the logs
        problematic_ids = [
            "550e8400-e29b-41d4-a716-446655440101",  # F1
            "550e8400-e29b-41d4-a716-446655440102",  # F2
            "550e8400-e29b-41d4-a716-446655440103",  # F3
            "550e8400-e29b-41d4-a716-446655440104",  # F4
            "f450f61f-2adf-4b01-b6ee-fed57014aa91",  # From logs
            "73e38b59-3290-4b7c-8600-07e3b341be0a",  # From logs
            "9273ffb5-cc06-45ff-ad48-2d6d5f7ad214",  # From logs
        ]
        
        print("Checking problematic table IDs:")
        for table_id in problematic_ids:
            table = db.query(Table).filter(Table.id == table_id).first()
            layout = db.query(TableLayout).filter(TableLayout.table_id == table_id).first()
            
            print(f"\nTable ID: {table_id}")
            if table:
                print(f"  Table found: {table.name}")
                print(f"  Room ID: {table.room_id}")
            else:
                print("  Table NOT found")
                
            if layout:
                print(f"  Layout found: {layout.id}")
                print(f"  Layout position: ({layout.x_position}, {layout.y_position})")
            else:
                print("  Layout NOT found")
        
        # Check all tables and their layouts
        print("\n\nAll tables and their layouts:")
        tables = db.query(Table).all()
        for table in tables:
            layout = db.query(TableLayout).filter(TableLayout.table_id == table.id).first()
            print(f"Table: {table.name} (ID: {table.id})")
            if layout:
                print(f"  Layout ID: {layout.id}")
            else:
                print("  NO LAYOUT")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_layout_issue() 