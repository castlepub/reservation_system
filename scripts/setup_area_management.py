#!/usr/bin/env python3
"""
Setup Area Management System
This script runs the migration and sets up default areas based on the German application structure.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.area_service import AreaService
from app.schemas.room import RoomCreate
from app.models.room import AreaType
import subprocess


def run_migration():
    """Run the area management migration"""
    print("🔄 Running area management migration...")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if result.returncode == 0:
            print("✅ Migration completed successfully")
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False


def setup_default_areas():
    """Setup default areas based on German application structure"""
    print("🔄 Setting up default areas...")
    
    db = SessionLocal()
    try:
        area_service = AreaService(db)
        
        # Check if areas already exist
        existing_areas = area_service.get_all_areas()
        if existing_areas:
            print(f"ℹ️  Areas already exist ({len(existing_areas)} found), updating with new structure...")
            
            # Update existing areas with new area management fields
            for area in existing_areas:
                if "Front" in area.name:
                    area_service.update_area(area.id, RoomCreate(
                        name=area.name,
                        description="Front section of the restaurant",
                        area_type=AreaType.INDOOR,
                        priority=4,
                        is_fallback_area=False,
                        display_order=0
                    ))
                elif "Middle" in area.name:
                    area_service.update_area(area.id, RoomCreate(
                        name=area.name,
                        description="Middle section of the restaurant",
                        area_type=AreaType.INDOOR,
                        priority=8,
                        is_fallback_area=False,
                        display_order=1
                    ))
                elif "Back" in area.name:
                    area_service.update_area(area.id, RoomCreate(
                        name=area.name,
                        description="Back section of the restaurant",
                        area_type=AreaType.INDOOR,
                        priority=3,
                        is_fallback_area=False,
                        display_order=2
                    ))
                elif "Biergarten" in area.name or "Beer Garden" in area.name:
                    area_service.update_area(area.id, RoomCreate(
                        name=area.name,
                        description="Outdoor seating area",
                        area_type=AreaType.OUTDOOR,
                        priority=8,
                        is_fallback_area=True,
                        display_order=3
                    ))
            
            print("✅ Updated existing areas with new structure")
            return True
        else:
            # Create new default areas
            default_areas = [
                {
                    "name": "Front Area",
                    "description": "Front section of the restaurant",
                    "area_type": AreaType.INDOOR,
                    "priority": 4,
                    "is_fallback_area": False,
                    "display_order": 0
                },
                {
                    "name": "Middle Area", 
                    "description": "Middle section of the restaurant",
                    "area_type": AreaType.INDOOR,
                    "priority": 8,
                    "is_fallback_area": False,
                    "display_order": 1
                },
                {
                    "name": "Back Area",
                    "description": "Back section of the restaurant", 
                    "area_type": AreaType.INDOOR,
                    "priority": 3,
                    "is_fallback_area": False,
                    "display_order": 2
                },
                {
                    "name": "Beer Garden - Winter Garden",
                    "description": "Outdoor seating area",
                    "area_type": AreaType.OUTDOOR,
                    "priority": 8,
                    "is_fallback_area": True,
                    "display_order": 3
                }
            ]
            
            created_areas = []
            for area_data in default_areas:
                area = area_service.create_area(RoomCreate(**area_data))
                created_areas.append(area)
                print(f"✅ Created area: {area.name} ({area.area_type}) - Priority: {area.priority}")
            
            print(f"✅ Created {len(created_areas)} default areas")
            return True
            
    except Exception as e:
        print(f"❌ Error setting up areas: {e}")
        return False
    finally:
        db.close()


def main():
    """Main setup function"""
    print("🚀 Setting up Area Management System...")
    print("=" * 50)
    
    # Run migration
    if not run_migration():
        print("❌ Setup failed at migration step")
        return False
    
    # Setup default areas
    if not setup_default_areas():
        print("❌ Setup failed at area setup step")
        return False
    
    print("=" * 50)
    print("✅ Area Management System setup completed successfully!")
    print("\n📋 What was added:")
    print("  • Area type categorization (Indoor/Outdoor/Shared)")
    print("  • Priority-based assignment system (1-10)")
    print("  • Fallback area support for weather conditions")
    print("  • Drag-and-drop area reordering")
    print("  • Default areas matching German application structure")
    print("\n🎯 Next steps:")
    print("  • Test the new area management API endpoints")
    print("  • Update the frontend to use the new area system")
    print("  • Implement the visual area management interface")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 