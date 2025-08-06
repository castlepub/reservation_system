from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, asc, desc
from typing import List, Optional, Dict, Any
from app.models.room import Room, AreaType
from app.models.table import Table
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse
from datetime import datetime
import uuid


class AreaService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_areas(self) -> List[RoomResponse]:
        """Get all areas ordered by display_order"""
        areas = self.db.query(Room).order_by(Room.display_order.asc()).all()
        return [RoomResponse.from_orm(area) for area in areas]

    def get_areas_by_type(self, area_type: AreaType) -> List[RoomResponse]:
        """Get areas filtered by type (indoor/outdoor/shared)"""
        areas = self.db.query(Room).filter(
            and_(
                Room.area_type == area_type,
                Room.active == True
            )
        ).order_by(Room.priority.asc()).all()
        return [RoomResponse.from_orm(area) for area in areas]

    def get_fallback_areas(self, original_room_id: str) -> List[RoomResponse]:
        """Get fallback areas for a given room (e.g., indoor alternatives for outdoor areas)"""
        fallback_areas = self.db.query(Room).filter(
            and_(
                Room.fallback_for == original_room_id,
                Room.active == True
            )
        ).order_by(Room.priority.asc()).all()
        return [RoomResponse.from_orm(area) for area in fallback_areas]

    def get_areas_by_priority(self, min_priority: int = 1, max_priority: int = 10) -> List[RoomResponse]:
        """Get areas within a priority range"""
        areas = self.db.query(Room).filter(
            and_(
                Room.priority >= min_priority,
                Room.priority <= max_priority,
                Room.active == True
            )
        ).order_by(Room.priority.asc()).all()
        return [RoomResponse.from_orm(area) for area in areas]

    def get_optimal_area_for_reservation(
        self, 
        party_size: int, 
        preferred_area_type: Optional[AreaType] = None
    ) -> Optional[RoomResponse]:
        """
        Find the optimal area for a reservation based on:
        - Party size capacity
        - Area type preference
        - Priority order
        """
        
        # Build query based on preferences
        query = self.db.query(Room).filter(Room.active == True)
        
        # Filter by area type if specified
        if preferred_area_type:
            query = query.filter(Room.area_type == preferred_area_type)
        
        # Order by priority (lower number = higher priority)
        areas = query.order_by(Room.priority.asc()).all()
        
        # Check capacity for each area
        for area in areas:
            total_capacity = self._get_area_capacity(area.id)
            if total_capacity >= party_size:
                return RoomResponse.from_orm(area)
        
        return None

    def _get_area_capacity(self, area_id: str) -> int:
        """Get total capacity of all tables in an area"""
        tables = self.db.query(Table).filter(
            and_(
                Table.room_id == area_id,
                Table.active == True
            )
        ).all()
        return sum(table.capacity for table in tables)

    def get_area_statistics(self) -> Dict[str, Any]:
        """Get statistics about all areas"""
        areas = self.db.query(Room).filter(Room.active == True).all()
        
        stats = {
            "total_areas": len(areas),
            "by_type": {
                "indoor": 0,
                "outdoor": 0,
                "shared": 0
            },
            "by_priority": {},
            "total_capacity": 0,
            "fallback_areas": 0
        }
        
        for area in areas:
            # Count by type
            stats["by_type"][area.area_type.value] += 1
            
            # Count by priority
            priority = area.priority
            if priority not in stats["by_priority"]:
                stats["by_priority"][priority] = 0
            stats["by_priority"][priority] += 1
            
            # Count fallback areas
            if area.is_fallback_area:
                stats["fallback_areas"] += 1
            
            # Calculate total capacity
            stats["total_capacity"] += self._get_area_capacity(area.id)
        
        return stats

    def get_area_recommendations(self, party_size: int, reservation_type: str) -> Dict[str, Any]:
        """Get area recommendations based on party size and reservation type"""
        
        # Determine preferred area type based on reservation type
        type_preferences = {
            "dinner": AreaType.INDOOR,
            "lunch": AreaType.INDOOR,
            "breakfast": AreaType.INDOOR,
            "drinks": AreaType.OUTDOOR,
            "party": AreaType.SHARED,
            "private": AreaType.INDOOR,
            "celebration": AreaType.SHARED,
            "team_event": AreaType.SHARED,
            "fun": AreaType.OUTDOOR,
            "special_event": AreaType.SHARED,
        }
        
        preferred_type = type_preferences.get(reservation_type, AreaType.INDOOR)
        
        # Get all areas
        all_areas = self.db.query(Room).filter(Room.active == True).order_by(Room.priority.asc()).all()
        
        recommendations = {
            "party_size": party_size,
            "reservation_type": reservation_type,
            "preferred_area_type": preferred_type.value,
            "suitable_areas": [],
            "alternative_areas": [],
            "fallback_areas": []
        }
        
        for area in all_areas:
            capacity = self._get_area_capacity(area.id)
            area_info = {
                "id": str(area.id),
                "name": area.name,
                "area_type": area.area_type.value,
                "priority": area.priority,
                "capacity": capacity,
                "is_fallback_area": area.is_fallback_area,
                "fallback_for": area.fallback_for
            }
            
            if capacity >= party_size:
                if area.area_type == preferred_type:
                    recommendations["suitable_areas"].append(area_info)
                else:
                    recommendations["alternative_areas"].append(area_info)
                
                if area.is_fallback_area:
                    recommendations["fallback_areas"].append(area_info)
        
        return recommendations 