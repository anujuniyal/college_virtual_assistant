"""
Optimized OTP Service for Fast Login Performance
"""
import secrets
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.extensions import db
from app.models import OTP
from app.config import Config
from flask import current_app

# Set up logger for background thread operations
logger = logging.getLogger(__name__)


class OptimizedOTPService:
    """Optimized OTP service with async email sending and caching"""
    
    # Simple in-memory cache for recent OTP attempts
    _otp_cache: Dict[str, Dict] = {}
    _cache_lock = threading.Lock()
    
    @staticmethod
    def generate_otp_fast(email: str) -> tuple[str, bool]:
        """
        Generate OTP and send email asynchronously for fast response
        Returns: (otp_code, success_indication)
        """
        start_time = time.time()
        
        # Generate OTP code
        otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Calculate expiry
        expires_at = datetime.utcnow() + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
        
        try:
            # Fast database operations
            with OptimizedOTPService._cache_lock:
                # Invalidate previous OTPs for this email (in cache first)
                if email in OptimizedOTPService._otp_cache:
                    OptimizedOTPService._otp_cache[email]['used'] = True
                
                # Cache the new OTP for quick verification
                OptimizedOTPService._otp_cache[email] = {
                    'otp_code': otp_code,
                    'expires_at': expires_at,
                    'used': False,
                    'created_at': datetime.utcnow()
                }
            
            # Database operations (minimal blocking)
            OTP.query.filter_by(email=email, used=False).update({'used': True})
            
            otp = OTP(
                email=email,
                otp_code=otp_code,
                expires_at=expires_at
            )
            db.session.add(otp)
            db.session.commit()
            
            # Send email asynchronously (non-blocking)
            OptimizedOTPService._send_email_async(email, otp_code)
            
            generation_time = round((time.time() - start_time) * 1000, 2)
            current_app.logger.info(f"OTP generated for {email} in {generation_time}ms")
            
            return otp_code, True
            
        except Exception as e:
            current_app.logger.error(f"OTP generation failed: {str(e)}")
            return otp_code, False
    
    @staticmethod
    def verify_otp_fast(email: str, otp_code: str) -> bool:
        """
        Verify OTP with cache-first approach for speed
        Returns: True if valid, False otherwise
        """
        start_time = time.time()
        
        try:
            # Check cache first (fastest)
            with OptimizedOTPService._cache_lock:
                if email in OptimizedOTPService._otp_cache:
                    cached_otp = OptimizedOTPService._otp_cache[email]
                    
                    if (not cached_otp['used'] and 
                        cached_otp['otp_code'] == otp_code and
                        cached_otp['expires_at'] > datetime.utcnow()):
                        
                        # Mark as used in cache
                        cached_otp['used'] = True
                        
                        verification_time = round((time.time() - start_time) * 1000, 2)
                        current_app.logger.info(f"OTP verified from cache for {email} in {verification_time}ms")
                        
                        # Update database asynchronously
                        OptimizedOTPService._mark_otp_used_async(email, otp_code)
                        
                        return True
            
            # Fallback to database if not in cache
            otp = OTP.query.filter_by(
                email=email,
                otp_code=otp_code,
                used=False
            ).order_by(OTP.created_at.desc()).first()
            
            if not otp:
                verification_time = round((time.time() - start_time) * 1000, 2)
                current_app.logger.warning(f"OTP not found for {email} in {verification_time}ms")
                return False
            
            if not otp.is_valid():
                verification_time = round((time.time() - start_time) * 1000, 2)
                current_app.logger.warning(f"OTP expired for {email} in {verification_time}ms")
                return False
            
            # Mark as used
            otp.used = True
            db.session.commit()
            
            # Update cache
            with OptimizedOTPService._cache_lock:
                if email in OptimizedOTPService._otp_cache:
                    OptimizedOTPService._otp_cache[email]['used'] = True
            
            verification_time = round((time.time() - start_time) * 1000, 2)
            current_app.logger.info(f"OTP verified from DB for {email} in {verification_time}ms")
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"OTP verification failed: {str(e)}")
            return False
    
    @staticmethod
    def _send_email_async(email: str, otp_code: str):
        """Send OTP email asynchronously"""
        def send_email():
            try:
                subject = "Your OTP for College Virtual Assistant"
                body = f"""
                Your OTP is: {otp_code}
                
                This OTP will expire in {Config.OTP_EXPIRY_MINUTES} minutes.
                
                If you didn't request this OTP, please ignore this email.
                """
                
                from app.services.background_email_service import send_email_background
                success = send_email_background(email, subject, body)
                
                if success:
                    logger.info(f"OTP email sent successfully to {email}")
                else:
                    logger.warning(f"Failed to send OTP email to {email}")
                    
            except Exception as e:
                logger.error(f"Async email sending failed: {str(e)}")
        
        # Start email sending in background thread
        email_thread = threading.Thread(target=send_email, daemon=True)
        email_thread.start()
    
    @staticmethod
    def _mark_otp_used_async(email: str, otp_code: str):
        """Mark OTP as used in database asynchronously"""
        def mark_used():
            try:
                from app.services.background_database_service import mark_otp_used_background
                success = mark_otp_used_background(email, otp_code)
                
                if success:
                    logger.info(f"OTP marked as used in background for {email}")
                else:
                    logger.warning(f"Failed to mark OTP as used in background for {email}")
                    
            except Exception as e:
                logger.error(f"Async OTP marking failed: {str(e)}")
        
        # Start database update in background thread
        db_thread = threading.Thread(target=mark_used, daemon=True)
        db_thread.start()
    
    @staticmethod
    def cleanup_cache():
        """Clean up expired OTPs from cache"""
        try:
            with OptimizedOTPService._cache_lock:
                current_time = datetime.utcnow()
                expired_emails = []
                
                for email, otp_data in OptimizedOTPService._otp_cache.items():
                    if otp_data['expires_at'] < current_time:
                        expired_emails.append(email)
                
                for email in expired_emails:
                    del OptimizedOTPService._otp_cache[email]
                
                if expired_emails:
                    current_app.logger.info(f"Cleaned up {len(expired_emails)} expired OTPs from cache")
                    
        except Exception as e:
            current_app.logger.error(f"Cache cleanup failed: {str(e)}")
    
    @staticmethod
    def get_cache_stats():
        """Get cache statistics for monitoring"""
        with OptimizedOTPService._cache_lock:
            total_cached = len(OptimizedOTPService._otp_cache)
            used_cached = sum(1 for otp in OptimizedOTPService._otp_cache.values() if otp['used'])
            active_cached = total_cached - used_cached
            
            return {
                'total_cached': total_cached,
                'active_cached': active_cached,
                'used_cached': used_cached
            }
