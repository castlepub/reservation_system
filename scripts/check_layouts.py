#!/usr/bin/env python3
"""
Script to check the current state of table layouts
"""
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.table_layout import TableLayout
from app.models.table import Table

def check_layouts():
    """Check the current state of table layouts"""
    db = next(get_db())
    
    try:
        # Get all layouts
        layouts = db.query(TableLayout).all()
        print(f"Found {len(layouts)} table layouts")
        
        # Get all tables
        tables = db.query(Table).all()
        print(f"Found {len(tables)} tables")
        
        # Check which tables have layouts
        layout_table_ids = {layout.table_id for layout in layouts}
        missing_layouts = []
        
        for table in tables:
            if table.id not in layout_table_ids:
                missing_layouts.append(table)
        
        print(f"Tables missing layouts: {len(missing_layouts)}")
        for table in missing_layouts:
            print(f"  - {table.name} (ID: {table.id})")
        
        # Show some layout examples
        print("\nLayout examples:")
        for layout in layouts[:5]:
            table = db.query(Table).filter(Table.id == layout.table_id).first()
            print(f"  Layout ID: {layout.id}")
            print(f"  Table ID: {layout.table_id}")
            print(f"  Table Name: {table.name if table else 'N/A'}")
            print(f"  Position: ({layout.x_position}, {layout.y_position})")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_layouts() 