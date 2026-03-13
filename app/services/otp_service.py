"""
OTP Service for Faculty Verification
"""
import secrets
from datetime import datetime, timedelta

from app.extensions import db
from app.models import OTP
from app.config import Config
from app.services.email_service import EmailService


class OTPService:
    """OTP generation and verification service"""
    
    @staticmethod
    def generate_otp(email: str) -> tuple[str, bool]:
        """
        Generate and send OTP
        Returns: (otp_code, success)
        """
        otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Calculate expiry
        expires_at = datetime.utcnow() + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
        
        # Invalidate previous OTPs for this email
        OTP.query.filter_by(email=email, used=False).update({'used': True})
        
        # Create new OTP
        otp = OTP(
            email=email,
            otp_code=otp_code,
            expires_at=expires_at
        )
        db.session.add(otp)
        db.session.commit()
        
        # Send email
        subject = "Your OTP for College Virtual Assistant"
        body = f"""
        Your OTP is: {otp_code}
        
        This OTP will expire in {Config.OTP_EXPIRY_MINUTES} minutes.
        
        If you didn't request this OTP, please ignore this email.
        """
        
        success = EmailService.send_email(email, subject, body)
        
        return otp_code, success
    
    @staticmethod
    def verify_otp(email: str, otp_code: str) -> bool:
        """
        Verify OTP
        Returns: True if valid, False otherwise
        """
        otp = OTP.query.filter_by(
            email=email,
            otp_code=otp_code,
            used=False
        ).order_by(OTP.created_at.desc()).first()
        
        if not otp:
            return False
        
        if not otp.is_valid():
            return False
        
        # Mark as used
        otp.used = True
        db.session.commit()
        
        return True
    
    @staticmethod
    def cleanup_expired_otps():
        """Cleanup expired OTPs"""
        expired_count = OTP.query.filter(OTP.expires_at < datetime.utcnow()).delete()
        db.session.commit()
        return expired_count
