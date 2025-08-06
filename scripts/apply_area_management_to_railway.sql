-- SQL script to add area management fields to rooms table
-- This can be applied directly to Railway database

-- Create the areatype enum
CREATE TYPE areatype AS ENUM ('indoor', 'outdoor', 'shared');

-- Add new columns to rooms table
ALTER TABLE rooms 
ADD COLUMN area_type areatype DEFAULT 'indoor',
ADD COLUMN priority INTEGER DEFAULT 1,
ADD COLUMN is_fallback_area BOOLEAN DEFAULT FALSE,
ADD COLUMN fallback_for TEXT,
ADD COLUMN display_order INTEGER DEFAULT 0;

-- Create index for better performance
CREATE INDEX idx_rooms_area_type ON rooms(area_type);
CREATE INDEX idx_rooms_priority ON rooms(priority);
CREATE INDEX idx_rooms_display_order ON rooms(display_order);

-- Update existing rooms to have proper area types and priorities
-- You can customize these based on your existing room names
UPDATE rooms 
SET area_type = CASE 
    WHEN name ILIKE '%outdoor%' OR name ILIKE '%terrace%' OR name ILIKE '%garden%' THEN 'outdoor'
    WHEN name ILIKE '%shared%' OR name ILIKE '%common%' THEN 'shared'
    ELSE 'indoor'
END,
priority = CASE 
    WHEN name ILIKE '%main%' OR name ILIKE '%primary%' THEN 1
    WHEN name ILIKE '%secondary%' THEN 2
    ELSE 3
END,
display_order = id;

-- Set up some default fallback areas
-- Update this based on your actual room setup
UPDATE rooms 
SET is_fallback_area = TRUE,
    fallback_for = 'outdoor'
WHERE area_type = 'indoor' 
AND (name ILIKE '%main%' OR name ILIKE '%primary%')
LIMIT 1;

-- Verify the changes
SELECT id, name, area_type, priority, is_fallback_area, fallback_for, display_order 
FROM rooms 
ORDER BY display_order, priority; 