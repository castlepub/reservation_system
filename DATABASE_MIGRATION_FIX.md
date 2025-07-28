# Database Migration Fix - Missing reservation_type Column

## Problem
Your production database is missing the `reservation_type` column in the `reservations` table, causing errors like:
```
ERROR: column reservations.reservation_type does not exist
```

## Quick Fix

### Option 1: Run the Standalone Script (Recommended)
```bash
python scripts/add_reservation_type_column.py
```

This script will:
- Check if the column already exists
- Create the enum type for reservation types  
- Add the `reservation_type` column with default value 'dining'
- Verify the migration was successful

### Option 2: Manual SQL (If needed)
If you prefer to run SQL directly:

```sql
-- Create the enum type
CREATE TYPE reservationtype AS ENUM (
    'dining', 'fun', 'team_event', 'birthday', 'party', 'special_event'
);

-- Add the column
ALTER TABLE reservations 
ADD COLUMN reservation_type reservationtype 
DEFAULT 'dining' NOT NULL;
```

## Requirements
- The script requires `psycopg2` package
- Set your `DATABASE_URL` or `PGURI` environment variable
- Database must be PostgreSQL

## After Running
- All existing reservations will have `reservation_type` set to 'dining'
- New reservations can use any of the available types
- The API errors should be resolved

## Available Reservation Types
- `dining` - Regular Dining
- `fun` - Fun Night Out  
- `team_event` - Team Event
- `birthday` - Birthday
- `party` - Party
- `special_event` - Special Event