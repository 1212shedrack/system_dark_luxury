from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from .form import CustomerRegisterForm
from .backends import EmailBackend, StaffNumberBackend, UsernameBackend

User = get_user_model()


# =========================
# SMART SINGLE LOGIN
# =========================
def login_view(request):
    error = None

    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '').strip()

        if not identifier or not password:
            error = 'Please enter your credentials and password.'
        else:
            # Detect credential type and pick backend
            if '@' in identifier:
                # Email → Admin
                backend = EmailBackend()
            elif identifier.isdigit():
                # All digits → Cashier staff number
                backend = StaffNumberBackend()
            else:
                # Plain text → Customer username
                backend = UsernameBackend()

            user = backend.authenticate(request,
                                        identifier=identifier,
                                        password=password)

            if user is not None:
                login(request, user,
                      backend=f'accounts.backends.{type(backend).__name__}')

                if user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'cashier':
                    return redirect('cashier_dashboard')
                else:
                    return redirect('customer_dashboard')
            else:
                error = 'Invalid credentials. Please try again.'

    return render(request, 'accounts/login.html', {'error': error})


# =========================
# REGISTER (CUSTOMER)
# =========================
def register(request):
    form = CustomerRegisterForm()

    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'customer'
            user.save()
            return redirect('login')

    return render(request, 'accounts/register.html', {'form': form})


# =========================
# FORGOT PASSWORD
# =========================
def forgot_password(request):
    message = None
    error = None

    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()

        # Find user by email (admin) or username (customer)
        user = None
        try:
            if '@' in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            error = 'No account found with those details.'

        if user and user.email:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = request.build_absolute_uri(
                f'/accounts/reset-password/{uid}/{token}/'
            )
            send_mail(
                subject='Password Reset — ShopOS',
                message=f"Click the link to reset your password:\n\n"
                        f"{reset_url}\n\n"
                        f"{reset_url}\n\n"
                        f"This link expires in 24 hours.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            message = 'Password reset link sent to your email.'
        elif user and not user.email:
            error = 'No email address linked to this account.'
            error += ' Contact your administrator.'

    return render(request, 'accounts/forgot_password.html', {
        'message': message,
        'error':   error,
    })


def reset_password(request, uidb64, token):
    error = None
    success = None

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        error = 'This reset link is invalid or has expired.'
        return render(request, 'accounts/reset_password.html',
                      {'error': error, 'invalid': True})

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if len(password1) < 8:
            error = 'Password must be at least 8 characters.'
        elif password1 != password2:
            error = 'Passwords do not match.'
        else:
            user.set_password(password1)
            user.save()
            success = 'Password updated successfully. You can now log in.'

    return render(request, 'accounts/reset_password.html', {
        'error':   error,
        'success': success,
        'uid':     uidb64,
        'token':   token,
    })


# =========================
# DASHBOARDS
# =========================
@login_required
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html')


@login_required
def cashier_dashboard(request):
    return render(request, 'accounts/cashier_dashboard.html')


@login_required
def customer_dashboard(request):
    return render(request, 'accounts/customer_dashboard.html')


# =========================
# LOGOUT
# =========================
def logout_view(request):
    logout(request)
    return redirect('login')
