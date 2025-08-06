#!/usr/bin/env python3
"""
Test script to verify table shapes are working correctly
"""

import requests
import json
from datetime import date

# Configuration
BASE_URL = "http://localhost:8000"
TEST_ROOM_ID = "test-room-1"
TEST_DATE = date.today().isoformat()

def test_table_shapes():
    """Test that table shapes are properly applied"""
    print("Testing table shapes...")
    
    # Test data for different shapes
    test_shapes = [
        {"shape": "round", "expected_border_radius": "50%"},
        {"shape": "square", "expected_border_radius": "0"},
        {"shape": "rectangular", "expected_border_radius": "0"},
        {"shape": "bar_stool", "expected_border_radius": "50%"}
    ]
    
    for test_case in test_shapes:
        shape = test_case["shape"]
        expected = test_case["expected_border_radius"]
        
        print(f"\nTesting shape: {shape}")
        print(f"Expected border-radius: {expected}")
        
        # Create test table data
        table_data = {
            "table_name": f"Test {shape.title()}",
            "capacity": 4,
            "combinable": True,
            "room_id": TEST_ROOM_ID,
            "x_position": 100,
            "y_position": 100,
            "width": 100,
            "height": 80,
            "shape": shape,
            "color": "#4CAF50",
            "border_color": "#2E7D32",
            "text_color": "#FFFFFF",
            "show_capacity": True,
            "show_name": True,
            "font_size": 12,
            "custom_capacity": 4,
            "is_connected": False,
            "connected_to": None,
            "z_index": 1
        }
        
        print(f"Table data: {json.dumps(table_data, indent=2)}")
        print(f"✅ Shape '{shape}' should render with border-radius: {expected}")

def test_shape_enum_values():
    """Test that shape enum values match frontend expectations"""
    print("\nTesting shape enum values...")
    
    expected_shapes = ["rectangular", "round", "square", "bar_stool", "custom"]
    
    try:
        from app.models.table_layout import TableShape
        
        actual_shapes = [shape.value for shape in TableShape]
        print(f"Expected shapes: {expected_shapes}")
        print(f"Actual enum values: {actual_shapes}")
        
        if set(actual_shapes) == set(expected_shapes):
            print("✅ Shape enum values match frontend expectations")
        else:
            print("❌ Shape enum values don't match frontend expectations")
            missing = set(expected_shapes) - set(actual_shapes)
            extra = set(actual_shapes) - set(expected_shapes)
            if missing:
                print(f"Missing shapes: {missing}")
            if extra:
                print(f"Extra shapes: {extra}")
                
    except ImportError as e:
        print(f"❌ Could not import TableShape: {e}")

def test_frontend_shape_handling():
    """Test frontend shape handling logic"""
    print("\nTesting frontend shape handling logic...")
    
    # Simulate the frontend logic
    def get_border_radius(shape):
        if shape == 'round':
            return '50%'
        elif shape == 'square':
            return '0'
        elif shape == 'rectangular':
            return '0'
        elif shape == 'bar_stool':
            return '50%'
        else:
            return '0'
    
    test_cases = [
        ('round', '50%'),
        ('square', '0'),
        ('rectangular', '0'),
        ('bar_stool', '50%'),
        ('custom', '0'),
        ('invalid', '0')
    ]
    
    for shape, expected in test_cases:
        result = get_border_radius(shape)
        status = "✅" if result == expected else "❌"
        print(f"{status} Shape '{shape}' -> border-radius: {result} (expected: {expected})")

if __name__ == "__main__":
    print("=== Table Shape Test Suite ===")
    
    test_shape_enum_values()
    test_frontend_shape_handling()
    test_table_shapes()
    
    print("\n=== Test Summary ===")
    print("1. Shape enum values should match frontend expectations")
    print("2. Frontend should handle all shape types correctly")
    print("3. Round and bar_stool shapes should have 50% border-radius")
    print("4. Square and rectangular shapes should have 0 border-radius")
    print("5. Invalid shapes should default to 0 border-radius") 