import csv
from datetime import timedelta
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from POS.models import Sale, SaleItem
from orders.models import Order
from products.models import Product


def get_date_range(request):
    """Parse date range from request or default to current month."""
    today = timezone.now().date()
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    period = request.GET.get('period', 'month')

    if date_from and date_to:
        try:
            from datetime import datetime
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to,   '%Y-%m-%d').date()
            period = 'custom'
        except ValueError:
            date_from = today.replace(day=1)
            date_to = today
    elif period == 'today':
        date_from = today
        date_to = today
    elif period == 'week':
        date_from = today - timedelta(days=today.weekday())
        date_to = today
    elif period == 'month':
        date_from = today.replace(day=1)
        date_to = today
    elif period == 'year':
        date_from = today.replace(month=1, day=1)
        date_to = today
    else:
        date_from = today.replace(day=1)
        date_to = today

    return date_from, date_to, period


@login_required
def report_overview(request):
    date_from, date_to, period = get_date_range(request)

    # ── POS Sales ──────────────────────────────────────
    pos_sales = Sale.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status=Sale.STATUS_COMPLETED
    )
    pos_revenue = pos_sales.aggregate(t=Sum('total_amount'))['t'] or 0
    pos_count = pos_sales.count()
    pos_refunds = Sale.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status=Sale.STATUS_REFUNDED
    ).count()

    # ── Orders ─────────────────────────────────────────
    orders = Order.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )
    completed_orders = orders.filter(status='completed')
    orders_revenue = completed_orders.aggregate(
        t=Sum('order_items__price'))['t'] or 0
    orders_count = orders.count()
    orders_completed = completed_orders.count()
    orders_cancelled = orders.filter(status='cancelled').count()
    orders_pending = orders.filter(status='pending').count()
    orders_confirmed = orders.filter(status='confirmed').count()
    orders_processing = orders.filter(status='processing').count()

    # ── Combined ───────────────────────────────────────
    total_revenue = float(pos_revenue) + float(orders_revenue)

    # ── Payment breakdown ──────────────────────────────
    cash_rev = pos_sales.filter(
        payment_method=Sale.PAYMENT_CASH
    ).aggregate(t=Sum('total_amount'))['t'] or 0
    mobile_rev = pos_sales.filter(
        payment_method=Sale.PAYMENT_MOBILE
    ).aggregate(t=Sum('total_amount'))['t'] or 0
    card_rev = pos_sales.filter(
        payment_method=Sale.PAYMENT_CARD
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    # ── Top products ───────────────────────────────────
    top_products = SaleItem.objects.filter(
        sale__created_at__date__gte=date_from,
        sale__created_at__date__lte=date_to,
        sale__status=Sale.STATUS_COMPLETED
    ).values('product__name').annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum('unit_price'),
    ).order_by('-total_qty')[:8]

    top_names = [p['product__name'] for p in top_products]
    top_qtys = [p['total_qty'] for p in top_products]

    # ── Daily revenue chart ────────────────────────────
    delta = (date_to - date_from).days + 1
    chart_days = min(delta, 30)
    chart_start = date_to - timedelta(days=chart_days - 1)

    chart_labels = []
    chart_pos = []
    chart_orders = []

    for i in range(chart_days):
        day = chart_start + timedelta(days=i)
        p = Sale.objects.filter(
            created_at__date=day,
            status=Sale.STATUS_COMPLETED
        ).aggregate(t=Sum('total_amount'))['t'] or 0

        o = Order.objects.filter(
            created_at__date=day,
            status='completed'
        ).aggregate(t=Sum('order_items__price'))['t'] or 0

        chart_labels.append(day.strftime('%d %b'))
        chart_pos.append(float(p))
        chart_orders.append(float(o))

    # ── Category breakdown ─────────────────────────────
    category_data = SaleItem.objects.filter(
        sale__created_at__date__gte=date_from,
        sale__created_at__date__lte=date_to,
        sale__status=Sale.STATUS_COMPLETED
    ).values('product__category__name').annotate(
        total=Sum('quantity')
    ).order_by('-total')[:6]

    cat_labels = [c['product__category__name'] or 'Uncategorised'
                  for c in category_data]
    cat_data = [c['total'] for c in category_data]

    # ── Stock report
    low_stock = Product.objects.filter(
        is_active=True, quantity__gt=0, quantity__lte=5
    ).order_by('quantity')
    out_of_stock = Product.objects.filter(is_active=True, quantity=0)
    total_stock_value = Product.objects.filter(
        is_active=True
    ).aggregate(
        val=Sum('price')
    )['val'] or 0

    # ── Recent sales table
    recent_sales = Sale.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status=Sale.STATUS_COMPLETED
    ).select_related('cashier').order_by('-created_at')[:15]

    return render(request, 'reports/overview.html', {
        # filters
        'period':           period,
        'date_from':        date_from,
        'date_to':          date_to,
        # pos stats
        'pos_revenue':      pos_revenue,
        'pos_count':        pos_count,
        'pos_refunds':      pos_refunds,
        # order stats
        'orders_revenue':   orders_revenue,
        'orders_count':     orders_count,
        'orders_completed': orders_completed,
        'orders_cancelled': orders_cancelled,
        'orders_pending':   orders_pending,
        'orders_confirmed': orders_confirmed,
        'orders_processing': orders_processing,
        # combined
        'total_revenue':    total_revenue,
        # payment
        'cash_rev':         cash_rev,
        'mobile_rev':       mobile_rev,
        'card_rev':         card_rev,
        # stock
        'low_stock':        low_stock,
        'out_of_stock':     out_of_stock,
        'total_stock_value': total_stock_value,
        # tables
        'recent_sales':     recent_sales,
        'top_products':     top_products,
        # charts
        # charts
        'chart_labels':  chart_labels,
        'chart_pos':     chart_pos,
        'chart_orders':  chart_orders,
        'top_names':     top_names,
        'top_qtys':      top_qtys,
        'cat_labels':    cat_labels,
        'cat_data':      cat_data,
        'pay_data':      [
                            float(cash_rev),
                            float(mobile_rev),
                            float(card_rev),
                         ],
        'ord_pending':    orders_pending,
        'ord_confirmed':  orders_confirmed,
        'ord_processing': orders_processing,
        'ord_completed':  orders_completed,
        'ord_cancelled':  orders_cancelled,
        })


@login_required
def export_csv(request):
    """Export filtered sales data as CSV."""
    date_from, date_to, period = get_date_range(request)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="sales_report_{date_from}_{date_to}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        'Sale Number', 'Date', 'Time', 'Cashier',
        'Payment Method', 'Total (TZS)', 'Status'
    ])

    sales = Sale.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    ).select_related('cashier').order_by('-created_at')

    for sale in sales:
        writer.writerow([
            sale.sale_number,
            sale.created_at.strftime('%d %b %Y'),
            sale.created_at.strftime('%H:%M'),
            sale.cashier.username,
            sale.get_payment_method_display(),
            sale.total_amount,
            sale.get_status_display(),
        ])

    return response
