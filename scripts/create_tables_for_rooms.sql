-- Tables for Front Room (room_id: 550e8400-e29b-41d4-a716-446655440001)
INSERT INTO tables (id, room_id, name, capacity, combinable, active, x, y, width, height, created_at, updated_at) VALUES
('table-f1-550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'F1', 4, true, true, 10, 10, 80, 60, NOW(), NOW()),
('table-f2-550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'F2', 4, true, true, 100, 10, 80, 60, NOW(), NOW()),
('table-f3-550e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'F3', 2, true, true, 190, 10, 60, 50, NOW(), NOW()),
('table-f4-550e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440001', 'F4', 6, true, true, 10, 80, 100, 70, NOW(), NOW());

-- Tables for Middle Room (room_id: 550e8400-e29b-41d4-a716-446655440002)
INSERT INTO tables (id, room_id, name, capacity, combinable, active, x, y, width, height, created_at, updated_at) VALUES
('table-m1-550e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440002', 'M1', 4, true, true, 10, 10, 80, 60, NOW(), NOW()),
('table-m2-550e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440002', 'M2', 4, true, true, 100, 10, 80, 60, NOW(), NOW()),
('table-m3-550e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440002', 'M3', 6, true, true, 190, 10, 100, 70, NOW(), NOW()),
('table-m4-550e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440002', 'M4', 8, true, true, 10, 80, 120, 80, NOW(), NOW()),
('table-m5-550e8400-e29b-41d4-a716-446655440009', '550e8400-e29b-41d4-a716-446655440002', 'M5', 2, true, true, 140, 80, 60, 50, NOW(), NOW()),
('table-m6-550e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440002', 'M6', 2, true, true, 210, 80, 60, 50, NOW(), NOW());

-- Tables for Back Room (room_id: 550e8400-e29b-41d4-a716-446655440003)
INSERT INTO tables (id, room_id, name, capacity, combinable, active, x, y, width, height, created_at, updated_at) VALUES
('table-b1-550e8400-e29b-41d4-a716-446655440011', '550e8400-e29b-41d4-a716-446655440003', 'B1', 4, true, true, 10, 10, 80, 60, NOW(), NOW()),
('table-b2-550e8400-e29b-41d4-a716-446655440012', '550e8400-e29b-41d4-a716-446655440003', 'B2', 6, true, true, 100, 10, 100, 70, NOW(), NOW()),
('table-b3-550e8400-e29b-41d4-a716-446655440013', '550e8400-e29b-41d4-a716-446655440003', 'B3', 8, true, true, 10, 80, 120, 80, NOW(), NOW()),
('table-b4-550e8400-e29b-41d4-a716-446655440014', '550e8400-e29b-41d4-a716-446655440003', 'B4', 10, false, true, 140, 10, 150, 120, NOW(), NOW());

-- Tables for Biergarten (room_id: 550e8400-e29b-41d4-a716-446655440004)
INSERT INTO tables (id, room_id, name, capacity, combinable, active, x, y, width, height, created_at, updated_at) VALUES
('table-bg1-550e8400-e29b-41d4-a716-446655440015', '550e8400-e29b-41d4-a716-446655440004', 'BG1', 6, true, true, 10, 10, 100, 70, NOW(), NOW()),
('table-bg2-550e8400-e29b-41d4-a716-446655440016', '550e8400-e29b-41d4-a716-446655440004', 'BG2', 6, true, true, 120, 10, 100, 70, NOW(), NOW()),
('table-bg3-550e8400-e29b-41d4-a716-446655440017', '550e8400-e29b-41d4-a716-446655440004', 'BG3', 8, true, true, 230, 10, 120, 80, NOW(), NOW()),
('table-bg4-550e8400-e29b-41d4-a716-446655440018', '550e8400-e29b-41d4-a716-446655440004', 'BG4', 8, true, true, 10, 90, 120, 80, NOW(), NOW()),
('table-bg5-550e8400-e29b-41d4-a716-446655440019', '550e8400-e29b-41d4-a716-446655440004', 'BG5', 10, true, true, 140, 90, 150, 90, NOW(), NOW()),
('table-bg6-550e8400-e29b-41d4-a716-446655440020', '550e8400-e29b-41d4-a716-446655440004', 'BG6', 12, false, true, 300, 90, 180, 100, NOW(), NOW());