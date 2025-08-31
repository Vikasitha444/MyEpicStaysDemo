from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from .models import UserMFA
from .forms import MFAVerificationForm, CustomAuthenticationForm, MFASetupForm
from django.contrib.auth.models import User

def home_view(request):
    """Home page view"""
    return render(request, 'home.html')

@login_required
def dashboard_view(request):
    """Dashboard view for authenticated users"""
    user_mfa, created = UserMFA.objects.get_or_create(user=request.user)
    context = {
        'user_mfa': user_mfa,
    }
    return render(request, 'dashboard.html', context)

@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'profile.html')

class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        user = form.get_user()
        user_mfa, created = UserMFA.objects.get_or_create(user=user)
        
        if user_mfa.is_mfa_enabled:
            # Store user ID in session for MFA verification
            self.request.session['pre_mfa_user_id'] = user.id
            return redirect('mfa_verify')
        else:
            # Normal login without MFA
            login(self.request, user)
            return redirect('dashboard')  # Change to your success URL

def mfa_verify_view(request):
    """Verify MFA token during login"""
    user_id = request.session.get('pre_mfa_user_id')
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        user_mfa = UserMFA.objects.get(user=user)
    except (User.DoesNotExist, UserMFA.DoesNotExist):
        return redirect('login')
    
    if request.method == 'POST':
        form = MFAVerificationForm(user=user, data=request.POST)
        if form.is_valid():
            # MFA verification successful
            login(request, user)
            del request.session['pre_mfa_user_id']  # Clean up session
            messages.success(request, 'Successfully logged in!')
            return redirect('dashboard')  # Change to your success URL
        else:
            messages.error(request, 'Invalid verification code.')
    else:
        form = MFAVerificationForm(user=user)
    
    return render(request, 'mfa/verify.html', {'form': form})

@login_required
def mfa_setup_view(request):
    """Setup MFA for user account"""
    user_mfa, created = UserMFA.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = MFASetupForm(request.POST)
        if form.is_valid():
            token = form.cleaned_data['token']
            if user_mfa.verify_token(token):
                user_mfa.is_mfa_enabled = True
                user_mfa.save()
                messages.success(request, 'MFA has been enabled successfully!')
                return redirect('mfa_backup_tokens')
            else:
                messages.error(request, 'Invalid verification code. Please try again.')
    else:
        form = MFASetupForm()
        if not user_mfa.secret_key:
            user_mfa.generate_secret_key()
    
    qr_code = user_mfa.get_qr_code()
    
    return render(request, 'mfa/setup.html', {
        'form': form,
        'qr_code': qr_code,
        'secret_key': user_mfa.secret_key
    })

@login_required
def mfa_backup_tokens_view(request):
    """Generate and display backup tokens"""
    user_mfa, created = UserMFA.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        backup_tokens = user_mfa.generate_backup_tokens()
        return render(request, 'mfa/backup_tokens.html', {
            'backup_tokens': backup_tokens,
            'show_tokens': True
        })
    
    return render(request, 'mfa/backup_tokens.html')

@login_required
def mfa_disable_view(request):
    """Disable MFA for user account"""
    if request.method == 'POST':
        user_mfa, created = UserMFA.objects.get_or_create(user=request.user)
        user_mfa.is_mfa_enabled = False
        user_mfa.secret_key = ''
        user_mfa.backup_tokens = []
        user_mfa.save()
        messages.success(request, 'MFA has been disabled.')
        return redirect('profile')  # Change to your profile URL
    
    return render(request, 'mfa/disable.html')
