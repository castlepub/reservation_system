from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import date

from app.core.database import get_db
from app.api.deps import require_chatbot_api_key
from app.services.reservation_service import ReservationService
from app.services.table_service import TableService
from app.models.room import Room

router = APIRouter(prefix="/chat", tags=["chatbot"], dependencies=[Depends(require_chatbot_api_key)])


@router.get("/rooms")
def get_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).filter(Room.active == True).all()
    table_service = TableService(db)
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "total_capacity": table_service._get_room_capacity(r.id),
        }
        for r in rooms
    ]


@router.get("/working-hours")
def get_working_hours_endpoint(target_date: date, db: Session = Depends(get_db)):
    reservation_service = ReservationService(db)
    # Use internal working hours service through availability call to get slots
    # Default party size 2 to derive slots
    slots_info = reservation_service.get_smart_availability(target_date, party_size=2)
    # Flatten open/close from settings (fallback)
    from app.core.config import settings
    open_h = getattr(settings, "OPENING_HOUR", 11)
    close_h = getattr(settings, "CLOSING_HOUR", 23)
    return {
        "open": f"{open_h:02d}:00",
        "close": f"{close_h:02d}:00",
        "slots": [slot["time"] for room in slots_info.get("rooms", []) for slot in room.get("available_time_slots", [])],
    }


@router.post("/availability")
def check_availability(payload: dict, db: Session = Depends(get_db)):
    try:
        target_date = date.fromisoformat(payload["date"])
        target_time = payload["time"]
        party_size = int(payload["party_size"])
        room_id = payload.get("room_id")

        reservation_service = ReservationService(db)
        availability = reservation_service.get_smart_availability(target_date, party_size)

        # Basic availability decision: any room has a slot equal to requested time
        available = any(
            any(slot.get("time") == target_time for slot in room.get("available_time_slots", []))
            for room in availability.get("rooms", [])
        )

        suggestions = []
        if not available:
            # Pick up to 3 nearest times across rooms
            for room in availability.get("rooms", [])[:3]:
                for slot in room.get("available_time_slots", [])[:3]:
                    suggestions.append({
                        "time": slot.get("time"),
                        "room_id": room.get("room_id"),
                        "room_name": room.get("room_name"),
                    })

        rooms = [
            {
                "id": room.get("room_id"),
                "name": room.get("room_name"),
                "total_capacity": room.get("total_capacity"),
            }
            for room in availability.get("rooms", [])
        ]

        return {"available": available, "rooms": rooms, "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reservations")
def create_reservation(payload: dict, idempotency_key: Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    try:
        # Simple idempotency (no store) – could be extended with Redis
        from app.schemas.reservation import ReservationCreate
        reservation = ReservationCreate(
            customer_name=payload["customer_name"],
            email=payload["email"],
            phone=payload["phone"],
            party_size=int(payload["party_size"]),
            date=date.fromisoformat(payload["date"]),
            time=payload["time"],
            reservation_type=payload.get("reservation_type", "dining"),
            notes=payload.get("notes"),
            room_id=payload.get("room_id"),
        )

        reservation_service = ReservationService(db)
        created = reservation_service.create_reservation(reservation)
        return created
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


