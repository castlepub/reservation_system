from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse
from app.services.area_service import AreaService
from app.models.room import AreaType
from app.api.deps import get_current_admin_user
from app.models.user import User

router = APIRouter()


@router.get("/areas", response_model=List[RoomResponse])
async def get_all_areas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all areas ordered by display order"""
    area_service = AreaService(db)
    return area_service.get_all_areas()


@router.get("/areas/type/{area_type}", response_model=List[RoomResponse])
async def get_areas_by_type(
    area_type: AreaType,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get areas filtered by type (indoor/outdoor/shared)"""
    area_service = AreaService(db)
    return area_service.get_areas_by_type(area_type)


@router.get("/areas/{area_id}/fallbacks", response_model=List[RoomResponse])
async def get_fallback_areas(
    area_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get fallback areas for a given area"""
    area_service = AreaService(db)
    return area_service.get_fallback_areas(area_id)


@router.post("/areas", response_model=RoomResponse)
async def create_area(
    area_data: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new area"""
    area_service = AreaService(db)
    return area_service.create_area(area_data)


@router.put("/areas/{area_id}", response_model=RoomResponse)
async def update_area(
    area_id: str,
    area_data: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update an existing area"""
    area_service = AreaService(db)
    updated_area = area_service.update_area(area_id, area_data)
    if not updated_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found"
        )
    return updated_area


@router.delete("/areas/{area_id}")
async def delete_area(
    area_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete an area (soft delete)"""
    area_service = AreaService(db)
    success = area_service.delete_area(area_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Area not found"
        )
    return {"message": "Area deleted successfully"}


@router.put("/areas/priorities")
async def update_area_priorities(
    priority_updates: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update priorities for multiple areas"""
    area_service = AreaService(db)
    updated_areas = area_service.update_area_priorities(priority_updates)
    return {
        "message": f"Updated priorities for {len(updated_areas)} areas",
        "updated_areas": updated_areas
    }


@router.put("/areas/reorder")
async def reorder_areas(
    new_order: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Reorder areas using drag-and-drop"""
    area_service = AreaService(db)
    reordered_areas = area_service.reorder_areas(new_order)
    return {
        "message": "Areas reordered successfully",
        "areas": reordered_areas
    }


@router.get("/areas/optimal")
async def get_optimal_area(
    party_size: int,
    preferred_area_type: AreaType = None,
    weather_condition: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Find the optimal area for a reservation"""
    area_service = AreaService(db)
    optimal_area = area_service.get_optimal_area_for_reservation(
        party_size, preferred_area_type, weather_condition
    )
    if not optimal_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No suitable area found for this party size"
        )
    return optimal_area


@router.get("/areas/statistics")
async def get_area_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get statistics about areas"""
    area_service = AreaService(db)
    return area_service.get_area_statistics()


@router.post("/areas/setup-default")
async def setup_default_areas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Setup default areas based on the German application structure"""
    area_service = AreaService(db)
    
    # Check if areas already exist
    existing_areas = area_service.get_all_areas()
    if existing_areas:
        return {"message": "Areas already exist, skipping setup"}
    
    # Create default areas based on German app structure
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
    
    return {
        "message": f"Created {len(created_areas)} default areas",
        "areas": created_areas
    } 