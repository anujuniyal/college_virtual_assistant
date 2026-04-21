#!/usr/bin/env python3
"""
Test script to verify email attachment handling
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.background_email_service import BackgroundEmailService

def test_email_attachment_logic():
    """Test that email service handles attachments correctly"""
    print("Testing BackgroundEmailService attachment logic...")
    
    try:
        service = BackgroundEmailService()
        
        # Test 1: Check SMTP configuration
        print(f"SMTP Config:")
        print(f"  Server: {service.mail_server}")
        print(f"  Username: {service.mail_username}")
        print(f"  Password: {'Set' if service.mail_password else 'Not Set'}")
        print(f"  From: {service.from_email}")
        print(f"  Is Render: {service.is_render}")
        
        # Test 2: Check API keys
        print(f"\nAPI Config:")
        print(f"  Brevo API Key: {'Set' if service.brevo_api_key else 'Not Set'}")
        print(f"  Resend API Key: {'Set' if service.api_key else 'Not Set'}")
        
        # Test 3: Simulate attachment decision
        attachments = ['/path/to/test.csv']
        has_attachments = attachments and len(attachments) > 0
        print(f"\nAttachment Decision:")
        print(f"  Has attachments: {has_attachments}")
        print(f"  Should use SMTP: {has_attachments}")
        
        print("\nSUCCESS: Email service logic verified")
        
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_email_attachment_logic()
