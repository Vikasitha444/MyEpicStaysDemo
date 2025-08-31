from django.contrib.auth.models import User
from django.db import models
import pyotp
import qrcode
from io import BytesIO
import base64
from django.contrib.auth.models import User

class UserMFA(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    secret_key = models.CharField(max_length=32, blank=True)
    is_mfa_enabled = models.BooleanField(default=False)
    backup_tokens = models.JSONField(default=list, blank=True)
    
    def generate_secret_key(self):
        """Generate a new secret key for TOTP"""
        self.secret_key = pyotp.random_base32()
        self.save()
        return self.secret_key
    
    def get_totp_uri(self):
        """Generate TOTP URI for QR code"""
        if not self.secret_key:
            self.generate_secret_key()
        
        return pyotp.totp.TOTP(self.secret_key).provisioning_uri(
            name=self.user.email,
            issuer_name="Your App Name"
        )
    
    def get_qr_code(self):
        """Generate QR code for authenticator app setup"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(self.get_totp_uri())
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_token(self, token):
        """Verify TOTP token"""
        if not self.secret_key:
            return False
        
        totp = pyotp.TOTP(self.secret_key)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_tokens(self):
        """Generate backup tokens for emergency access"""
        import secrets
        import string
        
        tokens = []
        for _ in range(10):
            token = ''.join(secrets.choice(string.digits) for _ in range(8))
            tokens.append(token)
        
        self.backup_tokens = tokens
        self.save()
        return tokens