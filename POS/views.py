import json
from decimal import Decimal
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from products.models import Product
from .models import Sale, SaleItem
from .decorators import cashier_or_admin_required


# ══════════════════════════════════════════════
# POS SCREEN
# ══════════════════════════════════════════════

@cashier_or_admin_required
def pos_screen(request):
    products = Product.objects.filter(
        is_active=True,
        quantity__gt=0
    ).order_by('category', 'name')

    today_sales = Sale.objects.filter(
        created_at__date=timezone.now().date(),
        status=Sale.STATUS_COMPLETED
    )
    today_total = today_sales.aggregate(
        t=Sum('total_amount'))['t'] or 0

    return render(request, 'pos/screen.html', {
        'products':    products,
        'today_count': today_sales.count(),
        'today_total': today_total,
    })


# ══════════════════════════════════════════════
# PROCESS SALE
# ══════════════════════════════════════════════

@cashier_or_admin_required
@require_POST
def process_sale(request):
    try:
        data = json.loads(request.body)
        cart_items = data.get('items', [])
        payment_method = data.get('payment_method', Sale.PAYMENT_CASH)
        amount_paid = Decimal(str(data.get('amount_paid', 0)))
        notes = data.get('notes', '')

        if not cart_items:
            return JsonResponse(
                {'success': False, 'error': 'Cart is empty.'}, status=400)

        with transaction.atomic():
            sale = Sale.objects.create(
                cashier=request.user,
                payment_method=payment_method,
                amount_paid=amount_paid,
                notes=notes,
            )

            total = Decimal('0')
            for entry in cart_items:
                product = get_object_or_404(
                    Product, pk=entry['product_id'], is_active=True)
                quantity = int(entry['quantity'])

                if quantity <= 0:
                    raise ValueError(
                        f"Invalid quantity for {product.name}.")
                if product.quantity < quantity:
                    raise ValueError(
                        f"Not enough stock for '{product.name}'. "
                        f"Available: {product.quantity}.")

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price,
                )
                total += product.price * quantity

                qty_before = product.quantity
                product.quantity -= quantity
                product.save(update_fields=['quantity'])

                # Log stock movement directly
                from inventory.models import StockMovement
                StockMovement.objects.create(
                    product=product,
                    movement_type='sale',
                    quantity=-quantity,
                    quantity_before=qty_before,
                    quantity_after=product.quantity,
                    reference=sale.sale_number,
                    created_by=request.user,
                )

            sale.total_amount = total
            sale.change_due = max(Decimal('0'), amount_paid - total)
            sale.save(update_fields=['total_amount', 'change_due'])

        return JsonResponse({
            'success':     True,
            'sale_id':     sale.id,
            'sale_number': sale.sale_number,
            'total':       str(sale.total_amount),
            'change':      str(sale.change_due),
        })

    except ValueError as e:
        return JsonResponse(
            {'success': False, 'error': str(e)}, status=400)
    except Exception:
        return JsonResponse(
            {'success': False,
             'error': 'Sale failed. Please try again.'}, status=500)


# ══════════════════════════════════════════════
# RECEIPT
# ══════════════════════════════════════════════

@cashier_or_admin_required
def receipt(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)
    return render(request, 'pos/receipt.html', {'sale': sale})


# ══════════════════════════════════════════════
# SALE HISTORY
# ══════════════════════════════════════════════

@cashier_or_admin_required
def sale_history(request):
    date_str = request.GET.get('date')
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            filter_date = timezone.now().date()
    else:
        filter_date = timezone.now().date()

    sales = Sale.objects.filter(
        created_at__date=filter_date
    ).prefetch_related('items__product')

    daily_total = sales.filter(
        status=Sale.STATUS_COMPLETED
    ).aggregate(t=Sum('total_amount'))['t'] or 0

    return render(request, 'pos/history.html', {
        'sales':       sales,
        'filter_date': filter_date,
        'daily_total': daily_total,
    })


# ══════════════════════════════════════════════
# REFUND
# ══════════════════════════════════════════════

@cashier_or_admin_required
@require_POST
def refund_sale(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)

    if sale.status == Sale.STATUS_REFUNDED:
        messages.error(request, 'This sale has already been refunded.')
        return redirect('pos:history')

    with transaction.atomic():
        for item in sale.items.all():
            qty_before = item.product.quantity
            item.product.quantity += item.quantity
            item.product.save(update_fields=['quantity'])

            from inventory.models import StockMovement
            StockMovement.objects.create(
                product=item.product,
                movement_type='refund',
                quantity=+item.quantity,
                quantity_before=qty_before,
                quantity_after=item.product.quantity,
                reference=sale.sale_number,
                created_by=request.user,
            )

        sale.status = Sale.STATUS_REFUNDED
        sale.save(update_fields=['status'])

    messages.success(
        request,
        f'Sale {sale.sale_number} refunded. Stock restored.')
    return redirect('pos:history')

# ══════════════════════════════════════════════
# AJAX — PRODUCT SEARCH
# ══════════════════════════════════════════════


@cashier_or_admin_required
@require_GET
def product_search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 1:
        return JsonResponse({'results': []})

    products = Product.objects.filter(
        is_active=True,
        quantity__gt=0,
    ).filter(
        Q(name__icontains=q) | Q(category__name__icontains=q)
    )[:10]

    return JsonResponse({'results': [{
        'id':       p.id,
        'name':     p.name,
        'price':    str(p.price),
        'quantity': p.quantity,
        'image':    p.image.url if p.image else '',
    } for p in products]})


# ══════════════════════════════════════════════
# AJAX — PRODUCT DETAIL
# ══════════════════════════════════════════════

@cashier_or_admin_required
@require_GET
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    return JsonResponse({
        'id':       product.id,
        'name':     product.name,
        'price':    str(product.price),
        'quantity': product.quantity,
        'image':    product.image.url if product.image else '',
    })
