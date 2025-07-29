from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_staff_user
from app.models.user import User
from app.schemas.layout import (
    TableLayoutCreate, TableLayoutUpdate, TableLayoutResponse,
    RoomLayoutCreate, RoomLayoutUpdate, RoomLayoutResponse,
    DailyViewResponse
)
from app.services.layout_service import LayoutService
from datetime import date, datetime

router = APIRouter(prefix="/api/layout", tags=["layout"])


@router.post("/tables", response_model=TableLayoutResponse)
def create_table_layout(
    layout_data: TableLayoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Create a new table layout"""
    try:
        layout_service = LayoutService(db)
        layout = layout_service.create_table_layout(layout_data)
        return layout
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/tables/{table_id}", response_model=TableLayoutResponse)
def update_table_layout(
    table_id: str,
    layout_data: TableLayoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Update a table layout"""
    layout_service = LayoutService(db)
    layout = layout_service.update_table_layout(table_id, layout_data)
    
    if not layout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table layout not found"
        )
    
    return layout


@router.get("/tables/{table_id}", response_model=TableLayoutResponse)
def get_table_layout(
    table_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get table layout by table ID"""
    layout_service = LayoutService(db)
    layout = layout_service.get_table_layout(table_id)
    
    if not layout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table layout not found"
        )
    
    return layout


@router.get("/rooms/{room_id}/tables", response_model=List[TableLayoutResponse])
def get_room_table_layouts(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get all table layouts for a room"""
    layout_service = LayoutService(db)
    layouts = layout_service.get_room_layouts(room_id)
    return layouts


@router.delete("/tables/{table_id}")
def delete_table_layout(
    table_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Delete a table layout"""
    layout_service = LayoutService(db)
    success = layout_service.delete_table_layout(table_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table layout not found"
        )
    
    return {"message": "Table layout deleted successfully"}


@router.post("/rooms", response_model=RoomLayoutResponse)
def create_room_layout(
    layout_data: RoomLayoutCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Create a new room layout"""
    try:
        layout_service = LayoutService(db)
        layout = layout_service.create_room_layout(layout_data)
        return layout
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/rooms/{room_id}", response_model=RoomLayoutResponse)
def update_room_layout(
    room_id: str,
    layout_data: RoomLayoutUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Update a room layout"""
    layout_service = LayoutService(db)
    layout = layout_service.update_room_layout(room_id, layout_data)
    
    if not layout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room layout not found"
        )
    
    return layout


@router.get("/rooms/{room_id}", response_model=RoomLayoutResponse)
def get_room_layout(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get room layout by room ID"""
    layout_service = LayoutService(db)
    layout = layout_service.get_room_layout(room_id)
    
    if not layout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room layout not found"
        )
    
    return layout


@router.get("/daily/{date}", response_model=DailyViewResponse)
def get_daily_view(
    date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get daily view with reservations and table layouts"""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    layout_service = LayoutService(db)
    daily_view = layout_service.get_daily_view(target_date)
    return daily_view


@router.get("/tables/{table_id}/reservations/{date}")
def get_table_reservations(
    table_id: str,
    date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get all reservations for a specific table on a specific date"""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    layout_service = LayoutService(db)
    reservations = layout_service.get_table_reservations(table_id, target_date)
    return {"reservations": reservations} 