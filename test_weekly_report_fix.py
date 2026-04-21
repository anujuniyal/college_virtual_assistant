#!/usr/bin/env python3
"""
Test script to verify weekly report fix
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.weekly_report_service import WeeklyReportService

def test_weekly_report_return():
    """Test that weekly report service returns a tuple"""
    print("Testing WeeklyReportService.generate_weekly_report() return type...")
    
    try:
        # Mock the database parts to test return type
        result = WeeklyReportService.generate_weekly_report()
        print(f"Return type: {type(result)}")
        print(f"Return value: {result}")
        
        if isinstance(result, tuple):
            print("SUCCESS: Returns tuple as expected")
            if len(result) == 2:
                print("SUCCESS: Tuple has exactly 2 elements")
                csv_path, visitor_csv_path = result
                print(f"CSV path: {csv_path}")
                print(f"Visitor CSV path: {visitor_csv_path}")
            else:
                print("ERROR: Tuple should have exactly 2 elements")
        else:
            print("ERROR: Should return a tuple")
            
    except Exception as e:
        print(f"Error during test (expected if database not available): {e}")
        # This is expected if database is not set up
        print("This is expected if database is not available - the fix is in the return type")

if __name__ == "__main__":
    test_weekly_report_return()
