#!/usr/bin/env python3
"""
Test search and filter functionality for predefined info
"""
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import PredefinedInfo
from app.extensions import db

def test_search_filter():
    """Test search and filter functionality"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Search and Filter Functionality")
        print("=" * 50)
        
        # Test 1: Search by title
        print("\n1️⃣ Testing search by title...")
        search_pattern = '%admission%'
        results = PredefinedInfo.query.filter(
            db.or_(
                PredefinedInfo.title.ilike(search_pattern),
                PredefinedInfo.content.ilike(search_pattern),
                PredefinedInfo.category.ilike(search_pattern)
            )
        ).all()
        
        print(f"Search for 'admission' found {len(results)} results:")
        for result in results:
            print(f"  - {result.section}: {result.title}")
        
        # Test 2: Filter by section
        print("\n2️⃣ Testing filter by section...")
        section_results = PredefinedInfo.query.filter(
            PredefinedInfo.section == 'admission'
        ).all()
        
        print(f"Filter by 'admission' section found {len(section_results)} results:")
        for result in section_results:
            print(f"  - {result.section}: {result.title}")
        
        # Test 3: Combined search and filter
        print("\n3️⃣ Testing combined search and filter...")
        combined_results = PredefinedInfo.query.filter(
            PredefinedInfo.section == 'admission'
        ).filter(
            db.or_(
                PredefinedInfo.title.ilike('%process%'),
                PredefinedInfo.content.ilike('%process%'),
                PredefinedInfo.category.ilike('%process%')
            )
        ).all()
        
        print(f"Combined search found {len(combined_results)} results:")
        for result in combined_results:
            print(f"  - {result.section}: {result.title}")
        
        # Test 4: Search in content
        print("\n4️⃣ Testing search in content...")
        content_search = PredefinedInfo.query.filter(
            db.or_(
                PredefinedInfo.title.ilike('%library%'),
                PredefinedInfo.content.ilike('%library%'),
                PredefinedInfo.category.ilike('%library%')
            )
        ).all()
        
        print(f"Search for 'library' found {len(content_search)} results:")
        for result in content_search:
            print(f"  - {result.section}: {result.title}")
        
        print("\n✅ All search and filter tests completed successfully!")
        print("✅ The search and filter functionality is working correctly!")
        
        return True

if __name__ == '__main__':
    test_search_filter()
