from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
# from inventory import models
from .form import CustomerRegisterForm
from .backends import EmailBackend, StaffNumberBackend, UsernameBackend
from django.utils import timezone
from django.db.models import Sum
from POS.models import Sale, SaleItem
from orders.models import Order
from products.models import Product
from django.contrib import messages
from django.core.paginator import Paginator


User = get_user_model()


# SMART SINGLE LOGIN


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
                # Check if account exists but is deactivated
                try:
                    if '@' in identifier:
                        u = User.objects.get(email=identifier)
                    elif identifier.isdigit():
                        u = User.objects.get(staff_number=identifier)
                    else:
                        u = User.objects.get(username=identifier)

                    if not u.is_active:
                        error = 'Your account has been deactivated.'
                        error += ' Contact your administrator.'
                    else:
                        error = 'Invalid credentials. Please try again.'
                except User.DoesNotExist:
                    error = 'Invalid credentials. Please try again.'

    return render(request, 'accounts/login.html', {'error': error})


# REGISTER (CUSTOMER)

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


# FORGOT PASSWORD

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


# DASHBOARDS

@login_required
def admin_dashboard(request):
    from datetime import timedelta
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Today POS
    today_sales = Sale.objects.filter(
        created_at__date=today,
        status=Sale.STATUS_COMPLETED
    )
    today_pos_revenue = today_sales.aggregate(
        t=Sum('total_amount'))['t'] or 0
    today_pos_count = today_sales.count()

    # Today orders revenue
    today_orders_rev = Order.objects.filter(
        created_at__date=today,
        status='completed'
    ).aggregate(t=Sum('order_items__price'))['t'] or 0

    # Today total revenue
    today_total_revenue = float(today_pos_revenue) + float(today_orders_rev)

    # Weekly revenue
    week_pos_rev = Sale.objects.filter(
        created_at__date__gte=week_start,
        status=Sale.STATUS_COMPLETED
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    week_orders_rev = Order.objects.filter(
        created_at__date__gte=week_start,
        status='completed'
    ).aggregate(t=Sum('order_items__price'))['t'] or 0

    week_total_revenue = float(week_pos_rev) + float(week_orders_rev)

    # Daily cash
    daily_cash = today_sales.filter(
        payment_method=Sale.PAYMENT_CASH
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    daily_mobile = today_sales.filter(
        payment_method=Sale.PAYMENT_MOBILE
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    daily_card = today_sales.filter(
        payment_method=Sale.PAYMENT_CARD
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    # Orders
    today_orders_count = Order.objects.filter(created_at__date=today).count()
    pending_orders = Order.objects.filter(status='pending').count()
    processing_orders = Order.objects.filter(status='processing').count()

    # Products
    low_stock = Product.objects.filter(
        is_active=True, quantity__gt=0, quantity__lte=5
    ).order_by('quantity')[:5]
    out_of_stock = Product.objects.filter(is_active=True, quantity=0).count()
    total_products = Product.objects.filter(is_active=True).count()

    # Recent
    recent_sales = Sale.objects.filter(
        status=Sale.STATUS_COMPLETED
    ).select_related('cashier')[:5]

    recent_orders = Order.objects.select_related(
        'customer'
    ).order_by('-created_at')[:5]

    # Last 7 days revenue chart
    chart_labels = []
    chart_pos = []
    chart_orders = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        pos_rev = Sale.objects.filter(
            created_at__date=day,
            status=Sale.STATUS_COMPLETED
        ).aggregate(t=Sum('total_amount'))['t'] or 0

        ord_rev = Order.objects.filter(
            created_at__date=day,
            status='completed'
        ).aggregate(t=Sum('order_items__price'))['t'] or 0

        chart_labels.append(day.strftime('%d %b'))
        chart_pos.append(float(pos_rev))
        chart_orders.append(float(ord_rev))

    # Top 5 products
    top_products = SaleItem.objects.values(
        'product__name'
    ).annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:5]

    top_names = [p['product__name'] for p in top_products]
    top_qtys = [p['total_qty'] for p in top_products]

    # Today payment methods pie
    today_pay_data = [
        float(daily_cash),
        float(daily_mobile),
        float(daily_card),
    ]

    # Month payment methods pie
    month_sales = Sale.objects.filter(
        created_at__date__gte=month_start,
        status=Sale.STATUS_COMPLETED
    )
    month_cash = month_sales.filter(
        payment_method=Sale.PAYMENT_CASH
    ).aggregate(t=Sum('total_amount'))['t'] or 0
    month_mobile = month_sales.filter(
        payment_method=Sale.PAYMENT_MOBILE
    ).aggregate(t=Sum('total_amount'))['t'] or 0
    month_card = month_sales.filter(
        payment_method=Sale.PAYMENT_CARD
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    month_pay_data = [
        float(month_cash),
        float(month_mobile),
        float(month_card),
    ]

    # Order status pie
    order_statuses = [
        'pending', 'confirmed', 'processing', 'completed', 'cancelled'
    ]
    order_status_data = [
        Order.objects.filter(status=s).count()
        for s in order_statuses
    ]

    return render(request, 'accounts/admin_dashboard.html', {
        # revenue cards
        'today_pos_revenue':    today_pos_revenue,
        'today_orders_rev':     today_orders_rev,
        'today_total_revenue':  today_total_revenue,
        'week_total_revenue':   week_total_revenue,
        'week_pos_rev':         week_pos_rev,
        'week_orders_rev':      week_orders_rev,
        'daily_cash':           daily_cash,
        'daily_mobile':         daily_mobile,
        'daily_card':           daily_card,
        # order stats
        'today_pos_count':      today_pos_count,
        'today_orders_count':   today_orders_count,
        'pending_orders':       pending_orders,
        'processing_orders':    processing_orders,
        # products
        'total_products':       total_products,
        'out_of_stock':         out_of_stock,
        'low_stock':            low_stock,
        # tables
        'recent_sales':         recent_sales,
        'recent_orders':        recent_orders,
        'top_products':         top_products,
        # charts
        'chart_labels':         chart_labels,
        'chart_pos':            chart_pos,
        'chart_orders':         chart_orders,
        'top_names':            top_names,
        'top_qtys':             top_qtys,
        'today_pay_data':       today_pay_data,
        'month_pay_data':       month_pay_data,
        'order_status_data':    order_status_data,
    })


@login_required
def cashier_dashboard(request):
    from datetime import timedelta

    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    today_sales = Sale.objects.filter(
        cashier=request.user,
        created_at__date=today,
        status=Sale.STATUS_COMPLETED
    )
    today_count = today_sales.count()
    today_revenue = today_sales.aggregate(
        t=Sum('total_amount'))['t'] or 0

    week_sales = Sale.objects.filter(
        cashier=request.user,
        created_at__date__gte=week_start,
        status=Sale.STATUS_COMPLETED
    )
    week_count = week_sales.count()
    week_revenue = week_sales.aggregate(
        t=Sum('total_amount'))['t'] or 0

    recent_sales = Sale.objects.filter(
        cashier=request.user,
        status=Sale.STATUS_COMPLETED
    ).prefetch_related('items__product')[:5]

    cash_total = today_sales.filter(
        payment_method=Sale.PAYMENT_CASH
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    mobile_total = today_sales.filter(
        payment_method=Sale.PAYMENT_MOBILE
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    card_total = today_sales.filter(
        payment_method=Sale.PAYMENT_CARD
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    chart_labels = []
    chart_revenue = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        rev = Sale.objects.filter(
            cashier=request.user,
            created_at__date=day,
            status=Sale.STATUS_COMPLETED
        ).aggregate(t=Sum('total_amount'))['t'] or 0
        chart_labels.append(day.strftime('%d %b'))
        chart_revenue.append(float(rev))

    return render(request, 'accounts/cashier_dashboard.html', {
        'today_count':   today_count,
        'today_revenue': today_revenue,
        'week_count':    week_count,
        'week_revenue':  week_revenue,
        'recent_sales':  recent_sales,
        'chart_labels':  chart_labels,
        'chart_revenue': chart_revenue,
        'cash_total':    cash_total,
        'mobile_total':  mobile_total,
        'card_total':    card_total,
    })


@login_required
def customer_dashboard(request):
    return render(request, 'accounts/customer_dashboard.html')

# LOGOUT


def logout_view(request):
    logout(request)
    return redirect('login')


# MANAGE CASHIERS
@login_required
def cashier_list(request):
    if request.user.role != 'admin':
        return redirect('admin_dashboard')

    cashiers = User.objects.filter(
        role='cashier'
    ).order_by('-date_joined')

    return render(request, 'accounts/cashier_list.html', {
        'cashiers': cashiers,
    })


@login_required
def cashier_add(request):
    if request.user.role != 'admin':
        return redirect('admin_dashboard')

    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        staff_number = request.POST.get('staff_number', '').strip()
        email = request.POST.get('email', '').strip() or None
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()

        if not username or not staff_number or not password:
            error = 'Username, staff number and password are required.'
        elif password != password2:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif User.objects.filter(username=username).exists():
            error = f'Username "{username}" is already taken.'
        elif User.objects.filter(staff_number=staff_number).exists():
            error = f'Staff number "{staff_number}" is already assigned.'
        else:
            User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
                role='cashier',
                staff_number=staff_number,
            )
            messages.success(
                request,
                f'Cashier "{username}" added successfully. '
                f'Staff number: {staff_number}'
            )
            return redirect('cashier_list')

    return render(request, 'accounts/cashier_form.html', {
        'error':  error,
        'action': 'Add',
    })


@login_required
def cashier_edit(request, pk):
    if request.user.role != 'admin':
        return redirect('admin_dashboard')

    cashier = get_object_or_404(User, pk=pk, role='cashier')
    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        staff_number = request.POST.get('staff_number', '').strip()
        email = request.POST.get('email', '').strip() or None

        if not username or not staff_number:
            error = 'Username and staff number are required.'
        elif User.objects.filter(
            username=username
        ).exclude(pk=pk).exists():
            error = f'Username "{username}" is already taken.'
        elif User.objects.filter(
            staff_number=staff_number
        ).exclude(pk=pk).exists():
            error = f'Staff number "{staff_number}" is already assigned.'
        else:
            cashier.username = username
            cashier.first_name = first_name
            cashier.last_name = last_name
            cashier.staff_number = staff_number
            cashier.email = email
            cashier.save()
            messages.success(request, f'Cashier "{username}" updated.')
            return redirect('cashier_list')

    return render(request, 'accounts/cashier_form.html', {
        'cashier': cashier,
        'error':   error,
        'action':  'Edit',
    })


@login_required
def cashier_toggle(request, pk):
    if request.user.role != 'admin':
        return redirect('admin_dashboard')

    cashier = get_object_or_404(User, pk=pk, role='cashier')
    cashier.is_active = not cashier.is_active
    cashier.save()

    status = 'activated' if cashier.is_active else 'deactivated'
    messages.success(request, f'Cashier "{cashier.username}" {status}.')
    return redirect('cashier_list')


@login_required
def cashier_reset_password(request, pk):
    if request.user.role != 'admin':
        return redirect('admin_dashboard')

    cashier = get_object_or_404(User, pk=pk, role='cashier')
    error = None

    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()

        if not password:
            error = 'Password is required.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif password != password2:
            error = 'Passwords do not match.'
        else:
            cashier.set_password(password)
            cashier.save()
            messages.success(
                request,
                f'Password for "{cashier.username}" reset successfully.'
            )
            return redirect('cashier_list')

    return render(request, 'accounts/cashier_reset_password.html', {
        'cashier': cashier,
        'error':   error,
    })


# MANAGE CUSTOMERS


@login_required
def customer_list(request):
    if request.user.role != 'admin':
        return redirect('admin_dashboard')

    search = request.GET.get('q', '').strip()
    customers = User.objects.filter(role='customer').order_by('-date_joined')

    if search:
        from django.db.models import Q
        customers = customers.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)

        )

    paginator = Paginator(customers, 20)
    page = request.GET.get('page')
    customers = paginator.get_page(page)

    return render(request, 'accounts/customer_list.html', {
        'customers': customers,
        'search':    search,
    })


@login_required
def customer_detail(request, pk):
    if request.user.role != 'admin':
        return redirect('admin_dashboard')

    from orders.models import Order
    customer = get_object_or_404(User, pk=pk, role='customer')
    orders = Order.objects.filter(
        customer=customer
    ).order_by('-created_at')

    total_spent = orders.filter(
        status='completed'
    ).aggregate(
        t=Sum('order_items__price')
    )['t'] or 0

    return render(request, 'accounts/customer_detail.html', {
        'customer':    customer,
        'orders':      orders,
        'total_spent': total_spent,
    })


@login_required
def customer_toggle(request, pk):
    if request.user.role != 'admin':
        return redirect('admin_dashboard')

    customer = get_object_or_404(User, pk=pk, role='customer')
    customer.is_active = not customer.is_active
    customer.save()

    status = 'activated' if customer.is_active else 'deactivated'
    messages.success(request, f'Customer "{customer.username}" {status}.')
    return redirect('customer_list')


# SETTINGS


@login_required
def shop_settings_view(request):
    if request.user.role != 'admin':
        return redirect('admin_dashboard')

    from .models import ShopSettings
    shop = ShopSettings.get()
    error = None
    success = None

    if request.method == 'POST':
        shop.shop_name = request.POST.get('shop_name', '').strip()
        shop.shop_address = request.POST.get('shop_address', '').strip()
        shop.shop_phone = request.POST.get('shop_phone', '').strip()
        shop.currency = request.POST.get('currency', 'TZS').strip()
        shop.receipt_footer = request.POST.get('receipt_footer', '').strip()
        shop.low_stock_alert = int(request.POST.get('low_stock_alert', 5))
        shop.items_per_page = int(request.POST.get('items_per_page', 20))

        # Handle logo upload
        if 'logo' in request.FILES:
            # Delete old logo file
            if shop.logo:
                import os
                if os.path.isfile(shop.logo.path):
                    os.remove(shop.logo.path)
            shop.logo = request.FILES['logo']

        # Handle logo removal
        if request.POST.get('remove_logo') == '1' and shop.logo:
            import os
            if os.path.isfile(shop.logo.path):
                os.remove(shop.logo.path)
            shop.logo = None

        shop.save()
        success = 'Settings saved successfully.'

    return render(request, 'accounts/settings.html', {
        'shop':    shop,
        'error':   error,
        'success': success,
    })


@login_required
def change_password(request):
    if request.user.role != 'admin':
        return redirect('admin_dashboard')

    error = None
    success = None

    if request.method == 'POST':
        current = request.POST.get('current_password', '')
        new_pwd = request.POST.get('new_password', '')
        confirm = request.POST.get('confirm_password', '')

        if not request.user.check_password(current):
            error = 'Current password is incorrect.'
        elif len(new_pwd) < 6:
            error = 'New password must be at least 6 characters.'
        elif new_pwd != confirm:
            error = 'New passwords do not match.'
        else:
            request.user.set_password(new_pwd)
            request.user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            success = 'Password changed successfully.'

    return render(request, 'accounts/change_password.html', {
        'error':   error,
        'success': success,
    })
