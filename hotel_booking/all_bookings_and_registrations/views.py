# all_bookings_and_registrations/views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import QRSession
import json
import secrets

def home_page(request):
    """Home page with QR code display"""
    # Generate new session
    session_id = secrets.token_hex(8)  # 16 character hex string
    
    # Create QR session
    qr_session = QRSession()
    qr_session.session_id = session_id
    qr_session.secret_key = qr_session.generate_secret()  # Generate base32 secret
    qr_session.save()
    
    # Generate QR code
    qr_code_data = qr_session.generate_qr_code()
    
    context = {
        'qr_code': qr_code_data,
        'session_id': session_id,
    }
    
    return render(request, 'home.html', context)

@csrf_exempt
def verify_qr_code(request):
    """Verify the QR code token"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            token = data.get('token')
            
            if not session_id or not token:
                return JsonResponse({
                    'success': False, 
                    'message': 'Session ID සහ Token දෙකම ඕනේ'
                })
            
            # Get QR session
            try:
                qr_session = QRSession.objects.get(session_id=session_id, is_verified=False)
            except QRSession.DoesNotExist:
                return JsonResponse({
                    'success': False, 
                    'message': 'අවලංගු session එකක්'
                })
            
            # Verify token
            if qr_session.verify_token(token):
                qr_session.is_verified = True
                qr_session.save()
                
                return JsonResponse({
                    'success': True, 
                    'message': 'සාර්ථකයි! QR Code හරියට verify වුනා!'
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