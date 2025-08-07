from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.layout_service import LayoutService
from app.schemas.layout import (
    TableLayoutCreate, TableLayoutUpdate, TableLayoutResponse,
    RoomLayoutCreate, RoomLayoutUpdate, RoomLayoutResponse,
    LayoutEditorData, TableSuggestion, LayoutExport, LayoutImport
)
from fastapi.responses import JSONResponse
import json

router = APIRouter()


@router.get("/editor/{room_id}")
async def get_layout_editor_data(
    room_id: str,
    target_date: date = Query(..., description="Target date for reservations"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LayoutEditorData:
    """Get comprehensive data for the layout editor"""
    try:
        layout_service = LayoutService(db)
        return layout_service.get_layout_editor_data(room_id, target_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load layout editor data: {str(e)}")


@router.post("/tables")
async def create_table_layout(
    layout_data: TableLayoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TableLayoutResponse:
    """Create a new table layout"""
    try:
        layout_service = LayoutService(db)
        layout = layout_service.create_table_layout(layout_data)
        return TableLayoutResponse.from_orm(layout)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create table layout: {str(e)}")


@router.put("/tables/{layout_id}")
async def update_table_layout(
    layout_id: str,
    layout_data: TableLayoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TableLayoutResponse:
    """Update an existing table layout"""
    try:
        layout_service = LayoutService(db)
        layout = layout_service.update_table_layout(layout_id, layout_data)
        if not layout:
            raise HTTPException(status_code=404, detail="Table layout not found")
        return TableLayoutResponse.from_orm(layout)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update table layout: {str(e)}")


@router.delete("/tables/{layout_id}")
async def delete_table_layout(
    layout_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a table layout"""
    try:
        layout_service = LayoutService(db)
        success = layout_service.delete_table_layout(layout_id)
        if not success:
            raise HTTPException(status_code=404, detail="Table layout not found")
        return {"message": "Table layout deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete table layout: {str(e)}")


@router.get("/tables/{layout_id}")
async def get_table_layout(
    layout_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TableLayoutResponse:
    """Get a specific table layout"""
    try:
        layout_service = LayoutService(db)
        layout = layout_service.get_table_layout(layout_id)
        if not layout:
            raise HTTPException(status_code=404, detail="Table layout not found")
        return TableLayoutResponse.from_orm(layout)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table layout: {str(e)}")


@router.get("/rooms/{room_id}/tables")
async def get_table_layouts_by_room(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TableLayoutResponse]:
    """Get all table layouts for a specific room"""
    try:
        layout_service = LayoutService(db)
        layouts = layout_service.get_table_layouts_by_room(room_id)
        return [TableLayoutResponse.from_orm(layout) for layout in layouts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table layouts: {str(e)}")


@router.post("/rooms")
async def create_room_layout(
    layout_data: RoomLayoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RoomLayoutResponse:
    """Create a new room layout"""
    try:
        layout_service = LayoutService(db)
        layout = layout_service.create_room_layout(layout_data)
        return RoomLayoutResponse.from_orm(layout)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create room layout: {str(e)}")


@router.put("/rooms/{room_id}")
async def update_room_layout(
    room_id: str,
    layout_data: RoomLayoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RoomLayoutResponse:
    """Update an existing room layout"""
    try:
        layout_service = LayoutService(db)
        layout = layout_service.update_room_layout(room_id, layout_data)
        if not layout:
            raise HTTPException(status_code=404, detail="Room layout not found")
        return RoomLayoutResponse.from_orm(layout)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update room layout: {str(e)}")


@router.get("/rooms/{room_id}")
async def get_room_layout(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> RoomLayoutResponse:
    """Get room layout for a specific room"""
    try:
        layout_service = LayoutService(db)
        layout = layout_service.get_room_layout(room_id)
        if not layout:
            raise HTTPException(status_code=404, detail="Room layout not found")
        return RoomLayoutResponse.from_orm(layout)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get room layout: {str(e)}")


@router.get("/suggestions/{room_id}")
async def get_table_suggestions(
    room_id: str,
    party_size: int = Query(..., ge=1, le=50),
    target_date: date = Query(...),
    target_time: str = Query(..., description="Time in HH:MM format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TableSuggestion]:
    """Get table assignment suggestions for a reservation"""
    try:
        layout_service = LayoutService(db)
        suggestions = layout_service.suggest_table_assignment(room_id, party_size, target_date, target_time)
        return [TableSuggestion(**suggestion) for suggestion in suggestions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table suggestions: {str(e)}")


@router.get("/export/{room_id}")
async def export_room_layout(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LayoutExport:
    """Export room layout as JSON"""
    try:
        layout_service = LayoutService(db)
        export_data = layout_service.export_room_layout(room_id)
        return LayoutExport(**export_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export room layout: {str(e)}")


@router.post("/import/{room_id}")
async def import_room_layout(
    room_id: str,
    import_data: LayoutImport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import room layout from JSON"""
    try:
        layout_service = LayoutService(db)
        success = layout_service.import_room_layout(room_id, import_data.layout_data)
        if success:
            return {"message": "Room layout imported successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to import room layout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import room layout: {str(e)}")


@router.get("/daily/{target_date}")
async def get_daily_layout_view(
    target_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get daily view with all room layouts and reservations"""
    try:
        layout_service = LayoutService(db)
        # Get all active rooms
        from app.models.room import Room
        from app.models.reservation import Reservation, ReservationTable
        from app.models.table import Table
        
        rooms = db.query(Room).filter(Room.active == True).all()
        
        daily_data = {
            "date": target_date.strftime("%Y-%m-%d"),
            "rooms": []
        }
        
        for room in rooms:
            # Get room layout data
            room_data = layout_service.get_layout_editor_data(str(room.id), target_date)
            
            # Get all reservations for this room on this date
            reservations = db.query(Reservation).filter(
                Reservation.room_id == room.id,
                Reservation.date == target_date
            ).all()
            
            # Convert reservations to proper format
            formatted_reservations = []
            for reservation in reservations:
                # Get table assignments for this reservation
                table_assignments = db.query(ReservationTable).filter(
                    ReservationTable.reservation_id == reservation.id
                ).all()
                
                assigned_tables = []
                for assignment in table_assignments:
                    table = db.query(Table).filter(Table.id == assignment.table_id).first()
                    if table:
                        assigned_tables.append({
                            "id": table.id,
                            "name": table.name,
                            "table_name": table.name
                        })
                
                formatted_reservation = {
                    "id": reservation.id,
                    "customer_name": reservation.customer_name,
                    "email": reservation.email,
                    "phone": reservation.phone,
                    "party_size": reservation.party_size,
                    "date": reservation.date.strftime("%Y-%m-%d"),
                    "time": str(reservation.time),
                    "duration_hours": reservation.duration_hours_safe,
                    "room_id": reservation.room_id,
                    "status": reservation.status.value,
                    "reservation_type": reservation.reservation_type.value,
                    "notes": reservation.notes,
                    "admin_notes": reservation.admin_notes,
                    "tables": assigned_tables
                }
                formatted_reservations.append(formatted_reservation)
            
            # Add room to daily data
            daily_data["rooms"].append({
                "id": room.id,
                "name": room.name,
                "layout": room_data.room_layout,
                "tables": room_data.tables,
                "reservations": formatted_reservations
            })
        
        return daily_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily layout view: {str(e)}") 