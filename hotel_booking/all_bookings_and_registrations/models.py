from django.db import models    
from django.contrib.auth.models import User 
import qrcode  
from io import BytesIO 
import base64 
import secrets 
import time 
import hmac,hashlib,struct 


class QRSession(models.Model):  
    session_id = models.CharField(max_length=100, unique=True) 
    secret_key = models.CharField(max_length=32)  
    is_verified = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True) 
    
    
    
    def generate_secret(self): 
        random_bytes = secrets.token_bytes(20) 
        secret_b32 = base64.b32encode(random_bytes).decode('utf-8')
        return secret_b32
    

    def generate_qr_code(self): 
        issuer = "MyEpicStaysDemo" 
        account_name = f"Enter This Code To Verify" 
        
        
        totp_uri = (f"otpauth://totp/{issuer}:{account_name}"f"?secret={self.secret_key}"f"&issuer={issuer}"f"&algorithm=SHA1"f"&digits=6"f"&period=30")
        
        
        
      
        qr = qrcode.QRCode(         
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)   
        qr.make(fit=True) 
        
        img = qr.make_image(fill_color="black", back_color="white") 
        
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}" 
    



    def generate_totp(self, time_step=None): 
        if time_step is None: 
            time_step = int(time.time()) // 30
            
        try:
            secret_key = self.secret_key.upper()
            missing_padding = len(secret_key) % 8
            if missing_padding:
                secret_key += '=' * (8 - missing_padding)
            
            secret_bytes = base64.b32decode(secret_key)
            
            
            time_bytes = struct.pack('>Q', time_step)
            
            
            hmac_digest = hmac.new(secret_bytes, time_bytes, hashlib.sha1).digest()
            
            
            offset = hmac_digest[19] & 0xf
            code = struct.unpack('>I', hmac_digest[offset:offset + 4])[0] & 0x7fffffff
            
            
            return str(code % 1000000).zfill(6)
            
        except Exception as e:
            print(f"TOTP generation error: {e}")
            return None
    
    def verify_token(self, token):
        """Verify TOTP token with time window tolerance"""
        current_time_step = int(time.time()) // 30
        
        
        for time_step in [current_time_step - 1, current_time_step, current_time_step + 1]:
            try:
                generated_token = self.generate_totp(time_step)
                if generated_token and generated_token == str(token).strip():
                    print(f"Token verified successfully: {generated_token}")
                    return True
            except Exception as e:
                print(f"Error in verify_token: {e}")
                continue
        
        print(f"Token verification failed for: {token}")
        return False
    
    def __str__(self):
        return f"QR Session {self.session_id}"

