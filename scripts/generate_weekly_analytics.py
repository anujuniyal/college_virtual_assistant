#!/usr/bin/env python3
"""
Script to generate weekly report analytics
Run this script to generate detailed analytics about data sent to admin in weekly reports
"""

import os
import sys
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.weekly_report_analytics import WeeklyReportAnalytics, get_weekly_report_analytics, get_admin_data_summary


def main():
    """Main function to generate analytics report"""
    
    print("=" * 60)
    print("WEEKLY REPORT ANALYTICS GENERATOR")
    print("=" * 60)
    
    try:
        # Initialize analytics service
        analytics = WeeklyReportAnalytics()
        
        # Generate detailed breakdown
        print("\n1. Generating detailed analytics breakdown...")
        breakdown = analytics.get_weekly_report_data_breakdown()
        
        # Generate admin summary
        print("2. Generating admin summary...")
        summary = analytics.get_data_summary_for_admin()
        
        # Save detailed report to JSON
        print("3. Saving detailed JSON report...")
        json_path = analytics.generate_analytics_report('json')
        print(f"   JSON report saved to: {json_path}")
        
        # Save summary report to CSV
        print("4. Saving summary CSV report...")
        csv_path = analytics.generate_analytics_report('csv')
        print(f"   CSV report saved to: {csv_path}")
        
        # Display summary
        print("\n" + "=" * 60)
        print("ANALYTICS SUMMARY")
        print("=" * 60)
        print(summary)
        
        # Display key metrics
        print("\n" + "=" * 60)
        print("KEY METRICS")
        print("=" * 60)
        
        email_data = breakdown['data_sent_to_admin']['email_report']['email_content']['data_fields']
        csv_data = breakdown['data_sent_to_admin']['csv_export']['data_structure']
        
        print(f"📧 Email Report Data:")
        for field in email_data:
            print(f"   - {field['field_name']}: {field['count']}")
        
        print(f"\n📊 CSV Export Data:")
        print(f"   - Records: {csv_data['row_count']}")
        print(f"   - File Size: {csv_data['data_size_bytes']} bytes")
        print(f"   - Columns: {len(csv_data['columns'])}")
        
        print(f"\n📈 Dashboard Metrics:")
        print(f"   - Total Data Points: {breakdown['data_sent_to_admin']['dashboard_metrics']['total_data_points']}")
        
        print(f"\n📋 Data Sources Used:")
        used_sources = [name for name, data in breakdown['data_sources_analysis'].items() 
                       if data.get('used_in_report')]
        for source in used_sources:
            data = breakdown['data_sources_analysis'][source]
            print(f"   - {source}: {data['weekly_records']} weekly records")
        
        print("\n" + "=" * 60)
        print("✅ Analytics report generated successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error generating analytics: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def quick_summary():
    """Generate quick summary without saving files"""
    
    print("Generating quick weekly report analytics summary...")
    
    try:
        # Get quick analytics
        breakdown = get_weekly_report_analytics()
        summary = get_admin_data_summary()
        
        print(summary)
        return True
        
    except Exception as e:
        print(f"Error generating quick summary: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate weekly report analytics')
    parser.add_argument('--quick', action='store_true', 
                       help='Generate quick summary without saving files')
    
    args = parser.parse_args()
    
    if args.quick:
        success = quick_summary()
    else:
        success = main()
    
    sys.exit(0 if success else 1)
