from django.db import models    #Django වල, Database Models (Tables) Import කරයි.
from django.contrib.auth.models import User #Django වල, inbuildම එන, User Table Structre එක Import කරයි.
import qrcode  #QR codes generate කරන Module එක Import කරයි
from io import BytesIO #Physical Memoryයට නොයවා, Images වැනි Files Handle කිරීමට භාවිතා කරයි
import base64 #Base64 වලින් Encode/Decode කිරීමට භාවිතා කරයි
import secrets #Django වල Secure විදිහට, random numbers generate කරන්න භාවිතා කරයි
import time #වෙලාව ආශ්‍රිත ගණනය කිරීම් වලට භාවිතා කරයි
import hmac,hashlib,struct #Time based OTP algorithm එකට අවශ්‍ය Moudles වේ

#Views වල භාවිතා වෙන, "QR Session" කියන Module එක මෙතන හදලා තියෙනවා.
#මේකෙදි කරලා තියෙන්නේ, QRSession කියලා Class එකක් හදලා, මේකට, Instent Varibales හා Functions ඇතුලත් කරලා තියෙන එක
class QRSession(models.Model):  
    session_id = models.CharField(max_length=100, unique=True) #Session ID Column එක Unique වෙන්න ඕනේ, Char වෙන්න ඕනේ
    secret_key = models.CharField(max_length=32)  #Secret_key Column එකේ උපරිම Length එක 32  වෙන්න ඕනේ
    is_verified = models.BooleanField(default=False) #is_verified Column එකේ, Boolean අගයන් විතරයි දාන්න පුළුවන්
    created_at = models.DateTimeField(auto_now_add=True) #created_at Column එකේ, දිනය හා Time එක දාන්න පුළුවන්
    


    #මෙතැනදී, Secret Key එකක් Genarate කරන්න Function එකක් ලියලා තියෙනවා
    #මේක ඕන වෙන්නේ, QR Code එක හදද්දී, සහ TOTP Code එක හදද්දී
    
    #QR Code එක ඇතුලේ තියෙන්නේ = Secret Key එකක් + Email එක + App Name එක
    #TOTP Code එක ඇතුලේ තියෙන්නේ = එකම(Same)Secret Key එක + Time එක

    def generate_secret(self): 
        random_bytes = secrets.token_bytes(20) 
        secret_b32 = base64.b32encode(random_bytes).decode('utf-8')
        return secret_b32

    

    def generate_qr_code(self): #QR code එක, Generate කරන Function එක වේ.
        issuer = "MyEpicStaysDemo" #Google Autheticator එකේ Display වෙන නම
        account_name = f"Enter This Code To Verify" #Google Autheticator එකේ Display වෙන අනිත් නම
        
        #Time based OTP එකේ, URI (URL) එක, Standerd Format එකට හදනවා.
        totp_uri = (f"otpauth://totp/{issuer}:{account_name}"f"?secret={self.secret_key}"f"&issuer={issuer}"f"&algorithm=SHA1"f"&digits=6"f"&period=30")
        
        
        
      
        qr = qrcode.QRCode(         #QR code object එකක් configure කරනවා
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)   #Standered Format එකට හදපු URI එක, QR Code එකට Embed කරනවා
        qr.make(fit=True) #QR Code එක හදනවා
        
        img = qr.make_image(fill_color="black", back_color="white") #QR code එකේ පාට වෙනස් කරනවා
        
        #Image එක String එකක් බවට පත් කරනවා. මේක Base64න් Encode කරලා තියෙන්නේ
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}" #QR Code එක Display කරන්න Web Page එකට යවනවා
    


    #මෙතැනදී, TOTP Key එකක් Genarate කරන්න Function එකක් ලියලා තියෙනවා.
    #TOTP Code එක ඇතුලේ තියෙන්නේ = එකම(Same)Secret Key එක + Time එක
    #මේක අංක 6ක Code එකක්.
    def generate_totp(self, time_step=None): #6-digit time-based code generate කරන්න
        if time_step is None: 
            time_step = int(time.time()) // 30 #දැන් time එක 30-second intervals වලට වෙන් කරනු ලැබේ.
            
        try:
            secret_key = self.secret_key.upper() #"Secret Key" එක මෙතැනදී uppercase කරනවා
            missing_padding = len(secret_key) % 8 #මෙතැනදී, Missing Padding කියන්නේ, "Secret Key" එකේ, Length එක 8ත වඩා අඩු නම්, එය Dummy Values වලින් පිරවීමටයි.
            if missing_padding:
                secret_key += '=' * (8 - missing_padding)
            
            secret_bytes = base64.b32decode(secret_key) #"Secret Key" එක, Base64 Bit Bytes Format එකට Convert කරයි.
            time_bytes = struct.pack('>Q', time_step) #Time එක Bytes වලට Convert කරයි
        
            hmac_digest = hmac.new(secret_bytes, time_bytes, hashlib.sha1).digest() #HMAC-SHA1 කියන algorithm එක භාවිතා කරලා, "secret_bytes" හා "Time Bytes" අගයන් Hash කරගනී
            offset = hmac_digest[19] & 0xf #Hash එකෙන් 4 bytes extract කරන්න offset එක ගණනය කරයි
            code = struct.unpack('>I', hmac_digest[offset:offset + 4])[0] & 0x7fffffff #4 bytes binary data එක integer එකක් බවට convert කරයි
            
            #6-digit code එකක් ලෙස format කර, Views එකට යවනු ලැබේ.
            return str(code % 1000000).zfill(6)
            
        except Exception as e:
            print(f"TOTP generation error: {e}")
            return None
    
    
    
    
    
    
    #මෙතැනදී, User විසින් Enter කළ, TOTP Key එක, නිවැරදිද බලන්න, Function එකක් ලියා තිබේ.
    def verify_token(self, token):
        current_time_step = int(time.time()) // 30  #දැන් time එක 30-second intervals වලට වෙන් කරනු ලැබේ.
        
        #User දැන් සිටින Window එක තප්පර ±30 ත් අතර කාලයක් බලා හිඳී.
        for time_step in [current_time_step - 1, current_time_step, current_time_step + 1]:
            try:
                generated_token = self.generate_totp(time_step) #Time Stamp එක දාලා, මෙතනදීත් TOTP අංකයක් නිර්මාණය කරගනී.
                if generated_token and generated_token == str(token).strip():  #User Enter කළ, TOTP අංකය සහ දැන් Genarate කරගත් TOTP අංකය, ගැලපේ නම්, 
                    print(f"Token verified successfully: {generated_token}") #මෙලෙස Print වේ.
                    return True
            except Exception as e:
                print(f"Error in verify_token: {e}")
                continue
        
        print(f"Token verification failed for: {token}")
        return False
    
    def __str__(self):
        return f"QR Session {self.session_id}"
