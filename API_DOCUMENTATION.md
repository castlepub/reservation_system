# The Castle Pub Reservation System - API Documentation

## Overview

This document describes the API endpoints for The Castle Pub Reservation System, a comprehensive restaurant reservation management system built with FastAPI and PostgreSQL.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://reservations.thecastle.de`

## Authentication

The system uses JWT (JSON Web Tokens) for authentication. Admin and staff endpoints require authentication.

### Getting a Token

```bash
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "admin",
    "role": "admin",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

### Using the Token

Include the token in the Authorization header:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Public API Endpoints

### 1. Check Availability

**Endpoint**: `GET /api/availability`

**Parameters**:
- `date` (string, required): Date in YYYY-MM-DD format
- `party_size` (integer, required): Number of people (1-20)
- `room_id` (string, optional): Specific room ID

**Example**:
```bash
GET /api/availability?date=2024-01-15&party_size=4&room_id=room-uuid
```

**Response**:
```json
{
  "date": "2024-01-15",
  "party_size": 4,
  "room_id": "room-uuid",
  "available_slots": [
    {
      "time": "18:00:00",
      "available_tables": [
        {
          "table_id": "table-uuid",
          "table_name": "T1",
          "capacity": 4
        }
      ],
      "total_capacity": 4
    },
    {
      "time": "19:30:00",
      "available_tables": [
        {
          "table_id": "table-uuid",
          "table_name": "T2",
          "capacity": 4
        }
      ],
      "total_capacity": 4
    }
  ]
}
```

### 2. Create Reservation

**Endpoint**: `POST /api/reservations`

**Request Body**:
```json
{
  "customer_name": "John Smith",
  "email": "john@example.com",
  "phone": "+1234567890",
  "party_size": 4,
  "date": "2024-01-15",
  "time": "19:30:00",
  "room_id": "room-uuid",
  "notes": "Birthday celebration"
}
```

**Response**:
```json
{
  "id": "reservation-uuid",
  "customer_name": "John Smith",
  "email": "john@example.com",
  "phone": "+1234567890",
  "party_size": 4,
  "date": "2024-01-15",
  "time": "19:30:00",
  "room_id": "room-uuid",
  "room_name": "Main Hall",
  "status": "confirmed",
  "notes": "Birthday celebration",
  "created_at": "2024-01-01T10:00:00",
  "updated_at": null,
  "tables": [
    {
      "table_id": "table-uuid",
      "table_name": "T1",
      "capacity": 4
    }
  ]
}
```

### 3. Get Rooms

**Endpoint**: `GET /api/rooms`

**Response**:
```json
[
  {
    "id": "room-uuid",
    "name": "Main Hall",
    "description": "The main dining area"
  },
  {
    "id": "room-uuid-2",
    "name": "Beer Garden",
    "description": "Outdoor seating area"
  }
]
```

### 4. Update Reservation (Token-based)

**Endpoint**: `PUT /api/reservations/{token}`

**Request Body**:
```json
{
  "party_size": 6,
  "time": "20:00:00",
  "notes": "Updated notes"
}
```

### 5. Cancel Reservation (Token-based)

**Endpoint**: `DELETE /api/reservations/{token}`

**Response**:
```json
{
  "message": "Reservation cancelled successfully"
}
```

## Admin API Endpoints

### Authentication Required

All admin endpoints require authentication with a valid JWT token.

### Room Management

#### Create Room
```bash
POST /api/admin/rooms
Authorization: Bearer <token>

{
  "name": "New Room",
  "description": "Room description"
}
```

#### Get All Rooms
```bash
GET /api/admin/rooms
Authorization: Bearer <token>
```

#### Update Room
```bash
PUT /api/admin/rooms/{room_id}
Authorization: Bearer <token>

{
  "name": "Updated Room Name",
  "active": false
}
```

### Table Management

#### Create Table
```bash
POST /api/admin/tables
Authorization: Bearer <token>

{
  "room_id": "room-uuid",
  "name": "T10",
  "capacity": 4,
  "combinable": true,
  "x": 100,
  "y": 100,
  "width": 80,
  "height": 60
}
```

#### Get Tables
```bash
GET /api/admin/tables?room_id=room-uuid
Authorization: Bearer <token>
```

#### Update Table
```bash
PUT /api/admin/tables/{table_id}
Authorization: Bearer <token>

{
  "capacity": 6,
  "combinable": false
}
```

### Reservation Management

#### Get Reservations
```bash
GET /api/admin/reservations?date=2024-01-15&room_id=room-uuid
Authorization: Bearer <token>
```

#### Get Specific Reservation
```bash
GET /api/admin/reservations/{reservation_id}
Authorization: Bearer <token>
```

#### Update Reservation
```bash
PUT /api/admin/reservations/{reservation_id}
Authorization: Bearer <token>

{
  "customer_name": "Updated Name",
  "party_size": 6
}
```

#### Cancel Reservation
```bash
DELETE /api/admin/reservations/{reservation_id}
Authorization: Bearer <token>
```

### PDF Generation

#### Generate Daily PDF
```bash
GET /api/admin/pdf/daily/2024-01-15?room_id=room-uuid
Authorization: Bearer <token>
```

Returns a PDF file with reservation slips for the specified date.

### User Management (Admin Only)

#### Create User
```bash
POST /api/admin/users
Authorization: Bearer <token>

{
  "username": "newuser",
  "password": "password123",
  "role": "staff"
}
```

#### Get All Users
```bash
GET /api/admin/users
Authorization: Bearer <token>
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## Business Rules

### Reservation Rules
- Party size: 1-20 people
- Minimum advance booking: 2 hours
- Maximum advance booking: 90 days
- Operating hours: 11:00 AM - 11:00 PM
- Reservations are made in 30-minute intervals

### Table Assignment
- Automatic table combination for optimal seating
- Tables can be marked as non-combinable
- System finds the best combination with minimal excess seats

### Email Notifications
- Confirmation emails sent automatically
- Cancel/edit links included in emails
- Tokens expire after 30 days

## Rate Limiting

Public endpoints are rate-limited to prevent abuse. Limits are:
- 100 requests per minute per IP address
- 1000 requests per hour per IP address

## Integration Examples

### Chatbot Integration

```python
import requests

# Check availability
response = requests.get(
    "https://reservations.thecastle.de/api/availability",
    params={
        "date": "2024-01-15",
        "party_size": 4
    }
)
available_slots = response.json()["available_slots"]

# Create reservation
reservation_data = {
    "customer_name": "John Smith",
    "email": "john@example.com",
    "phone": "+1234567890",
    "party_size": 4,
    "date": "2024-01-15",
    "time": "19:30:00",
    "room_id": "room-uuid"
}

response = requests.post(
    "https://reservations.thecastle.de/api/reservations",
    json=reservation_data
)
reservation = response.json()
```

### Website Integration

```javascript
// Check availability
async function checkAvailability(date, partySize) {
    const response = await fetch(
        `/api/availability?date=${date}&party_size=${partySize}`
    );
    return await response.json();
}

// Create reservation
async function createReservation(reservationData) {
    const response = await fetch('/api/reservations', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(reservationData)
    });
    return await response.json();
}
```

## Support

For API support or questions, contact:
- Email: tech@thecastle.de
- Documentation: https://reservations.thecastle.de/docs
- Interactive API docs: https://reservations.thecastle.de/redoc 