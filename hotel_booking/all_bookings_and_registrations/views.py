from django.shortcuts import render  # Django වල HTML templates return කරන්න භාවිතා කරයි
from django.http import JsonResponse # JSON responses යවන්න භාවිතා කරයි
from django.views.decorators.csrf import csrf_exempt # CSRF protection disable කරන්න decorator එක import කරනවා
from .models import QRSession # "models.py" file එකේ "QRSession model" එක import කිරීමට භාවිතා කරයි
import json # JSON data handle කරන්න භාවිතා කරයි
import secrets #Django වල Secure විදිහට, random numbers generate කරන්න භාවිතා කරයි

def home_page(request): #User Home Page එකට ගියාම වෙන දේ මෙතන Handle කරයි
    
    qr_session = QRSession() #QR Session Function එකට Call කර, "QR Session()"" වෙනුවට, "qr_session" නමට භාවිතයේ පහසුවට ආදේශ කිරීමට භාවිතා කරයි
    
    #QR session එක Genarate කිරීමට, Function එකට, අදාළ වූ, දත්ත මෙතනින් ලබා දෙනු ලැබේ
    session_id = secrets.token_hex(8)  # 8 bytes hexadecimal token එකක් generate කරනවා (length එක 16 characters)
    
    qr_session.session_id = session_id #Generate කරපු session_id එක assign කිරීමට භාවිතා කරයි
    qr_session.secret_key = qr_session.generate_secret()  #secret key එක generate කිරීමට භාවිතා කරයි
    qr_session.save() #QR session එක save කරනවා
    
    
    qr_code_data = qr_session.generate_qr_code() #Save කරනු ලැබූ දත්ත භාවිතයෙන්, QR Code එක Genarate කරයි.
    
    context = {
        'qr_code': qr_code_data, #Template එකට QR code එකේ Data Pass කිරීමට භාවිතා කරයි
        'session_id': session_id, #Template එකට Session ID එක Data Pass කිරීමට භාවිතා කරයි
    }
    
    return render(request, 'home.html', context) #home.html template එක data, pass කිරීමට භාවිතා කරයි.




#Defulat Django වලට එන, "CSRF protection" එක Disable කිරීමට සහ Display කිරීමට යන, QR Code, එක, Display කිරීමට පෙර, Verify කිරීමට මේ Function එක භාවතා කරයි
#Verify කරනවා කියලා බලන්නේ, QR Code එකේ, "session_id" එකයි, "Token(TOTP එක)" එකයි තියෙනවද කියලා.

@csrf_exempt #CSRF protection එක Disable කිරීමට භාවිතා වේ.
def verify_qr_code(request): # QR code verify function එක වේ
    
    if request.method == 'POST': # පළමුව, Template එකට ආව Request එක POST method එකක්ද කියලා check කිරීමට භාවිතා කරයි.
        try:
            data = json.loads(request.body) # එවපු Request එකේ, JSON Fromat එකෙන් හදපු Data, Python වලට කියවා ගත හැකි ආකාරයට Convert කරගැනීමට භාව්තා කරයි.
            session_id = data.get('session_id') # "session_id" value එක extract කිරීමට භාවිතා කරයි.
            token = data.get('token') #"token (TOTP එක)" එකේ value එක extract කිරීමට භාවිතා කරයි.
            
            # Session_id හෝ token (TOTP එක) දෙකෙන් එකක් හරි missing නම්,
            if not session_id or not token: 
                return JsonResponse({
                    'success': False, 
                    'message': 'Session ID සහ Token  දෙකම ඕනේ' # Session ID එකයි, Token (TOTP එක) එකයි, දෙකම ඕනේ කියා කියයි.
                })
            
            # එසේ, "Session_id" හෝ "Token" එක යන දෙකම තිබේ නම්,
            try:
                qr_session = QRSession.objects.get(session_id=session_id, is_verified=False)  #
            except QRSession.DoesNotExist: #"QR Session()" කියන Function එකම නැත්නම්,
                return JsonResponse({
                    'success': False, 
                    'message': 'අවලංගු session එකක්' #මෙහෙම Display කරන්න
                })
            
            # "qr_session" එකේ, "verify_token" Function එකට, Token(TOTP එක) Code එක දැම්මම, ලැබෙන උත්තරේ TRUE නම්,
            if qr_session.verify_token(token):
                qr_session.is_verified = True   #"is_verified" field එක True වේ
                qr_session.save()   # QR session එක Database එකට Save වේ.
                
                return JsonResponse({
                    'success': True, 
                    'message': 'සාර්ථකයි! QR Code හරියට verify වුනා!' # Success JSON response එකක් return කරනවා
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'message': 'වැරදි code එකක්. නැවත try කරන්න.'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'POST method එක පමණයි allow'})