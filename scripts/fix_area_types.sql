-- Fix area types and priorities for existing rooms
-- This script properly sets the area types using the enum

-- Update Biergarten to outdoor type
UPDATE rooms 
SET area_type = 'outdoor'::areatype,
    priority = 1,
    display_order = 4
WHERE name = 'Biergarten';

-- Update other rooms with better priorities
UPDATE rooms 
SET area_type = 'indoor'::areatype,
    priority = CASE 
        WHEN name = 'Front Room' THEN 1
        WHEN name = 'Middle Room' THEN 2
        WHEN name = 'Back Room' THEN 3
        ELSE 4
    END,
    display_order = CASE 
        WHEN name = 'Front Room' THEN 1
        WHEN name = 'Middle Room' THEN 2
        WHEN name = 'Back Room' THEN 3
        WHEN name = 'Biergarten' THEN 4
        ELSE 5
    END
WHERE name IN ('Front Room', 'Middle Room', 'Back Room');

-- Set up fallback areas
UPDATE rooms 
SET is_fallback_area = TRUE,
    fallback_for = 'outdoor'
WHERE name = 'Front Room';

-- Verify the final state
SELECT id, name, area_type, priority, is_fallback_area, fallback_for, display_order 
FROM rooms 
ORDER BY display_order, priority; 