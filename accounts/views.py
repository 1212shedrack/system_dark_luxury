from django.shortcuts import render, redirect
from .form import CustomerRegisterForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


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
            return redirect('customer_login')

    return render(request, 'accounts/register.html', {'form': form})

# =========================
# ADMIN LOGIN
# =========================


def admin_login(request):
    error = None
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is not None:
            if user.is_superuser or user.role == 'admin':
                login(request, user)
                return redirect('admin_dashboard')
            else:
                error = 'Access denied. Admin credentials required.'
        else:
            error = 'Invalid username or password.'

    return render(request, 'accounts/admin_login.html', {'error': error})


# =========================
# CASHIER LOGIN
# =========================
def cashier_login(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.role == 'cashier':
                login(request, user)
                return redirect('cashier_dashboard')
            else:
                error = 'Access denied. Cashier credentials required.'
        else:
            error = 'Invalid username or password.'

    return render(request, 'accounts/cashier_login.html', {'error': error})


# =========================
# CUSTOMER LOGIN
# =========================
def customer_login(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.role == 'customer':
                login(request, user)
                return redirect('customer_dashboard')
            else:
                error = 'This login is only for customers.'
        else:
            error = 'Invalid username or password.'

    return render(request, 'accounts/login.html', {'error': error})

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

# logout view


def logout_view(request):
    # Save role before logging out
    role = None
    if request.user.is_authenticated:
        role = request.user.role

    logout(request)

    if role == 'admin':
        return redirect('admin_login')
    elif role == 'cashier':
        return redirect('cashier_login')
    else:
        return redirect('customer_login')
