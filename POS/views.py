import json
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from accounts import models
from orders import models
from products.models import Product
# from inventory.models import StockMovement
from .models import Sale, SaleItem
from .decorators import cashier_or_admin_required


@cashier_or_admin_required
def pos_screen(request):
    """Main POS terminal screen."""
    products = Product.objects.filter(is_active=True,
                                      quantity__gt=0).order_by('category',
                                                               'name')
    today_sales = Sale.objects.filter(
        created_at__date=timezone.now().date(),
        status=Sale.STATUS_COMPLETED
    )
    today_total = sum(s.total_amount for s in today_sales)
    return render(request, 'pos/screen.html', {
        'products':    products,
        'today_count': today_sales.count(),
        'today_total': today_total,
    })


@cashier_or_admin_required
@require_POST
def process_sale(request):
    """
    Receive POS cart as JSON, validate quantity, create Sale + SaleItems,
    trigger inventory reduction via signal, return sale_id for receipt.
    """
    try:
        data = json.loads(request.body)
        cart_items = data.get('items', [])
        payment_method = data.get('payment_method', Sale.PAYMENT_CASH)
        amount_paid = Decimal(str(data.get('amount_paid', 0)))
        notes = data.get('notes', '')

        if not cart_items:
            return JsonResponse({'success': False,
                                 'error': 'Cart is empty.'}, status=400)

        with transaction.atomic():
            sale = Sale.objects.create(
                cashier=request.user,
                payment_method=payment_method,
                amount_paid=amount_paid,
                notes=notes,
            )

            total = Decimal('0')
            for entry in cart_items:
                product = get_object_or_404(Product,
                                            pk=entry['product_id'],
                                            is_active=True)
                quantity = int(entry['quantity'])

                if quantity <= 0:
                    raise ValueError(f"Invalid quantity for {product.name}.")
                if product.quantity < quantity:
                    raise ValueError(f"Not enough quantity for '{product.name}'. Available: {product.quantity}.")

                unit_price = product.price
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                )
                total += unit_price * quantity

                # Reduce stock directly
                # (signal also fires via post_save on SaleItem)
                product.quantity -= quantity
                product.save(update_fields=['quantity'])

            sale.total_amount = total
            sale.change_due = max(Decimal('0'), amount_paid - total)
            sale.save(update_fields=['total_amount', 'change_due'])

        return JsonResponse({
            'success':    True,
            'sale_id':    sale.id,
            'sale_number': sale.sale_number,
            'total':      str(sale.total_amount),
            'change':     str(sale.change_due),
        })

    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': 'Sale failed. Please try again.'}, status=500)


@cashier_or_admin_required
def receipt(request, sale_id):
    """Receipt page — printable and shareable."""
    sale = get_object_or_404(Sale, pk=sale_id)
    return render(request, 'pos/receipt.html', {'sale': sale})


@cashier_or_admin_required
def sale_history(request):
    """Cashier's daily sales list."""
    date_str = request.GET.get('date')
    if date_str:
        try:
            from datetime import datetime
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            filter_date = timezone.now().date()
    else:
        filter_date = timezone.now().date()

    sales = Sale.objects.filter(
        created_at__date=filter_date
    ).prefetch_related('items__product')

    daily_total = sum(s.total_amount for s in sales
                      if s.status == Sale.STATUS_COMPLETED)

    return render(request, 'pos/history.html', {
        'sales':       sales,
        'filter_date': filter_date,
        'daily_total': daily_total,
    })


@cashier_or_admin_required
@require_POST
def refund_sale(request, sale_id):
    """Mark a sale as refunded and restore quantity."""
    sale = get_object_or_404(Sale, pk=sale_id)

    if sale.status == Sale.STATUS_REFUNDED:
        messages.error(request, 'This sale has already been refunded.')
        return redirect('pos:history')

    with transaction.atomic():
        for item in sale.items.all():
            item.product.quantity += item.quantity
            item.product.save(update_fields=['quantity'])

        sale.status = Sale.STATUS_REFUNDED
        sale.save(update_fields=['status'])

    messages.success(request, f'Sale {sale.sale_number} refunded. Quantity restored.')
    return redirect('pos:history')


# ── AJAX endpoints for product search and details 

@cashier_or_admin_required
@require_GET
def product_search(request):
    """Search products by name or SKU for POS quick-add."""
    q = request.GET.get('q', '').strip()
    if len(q) < 1:
        return JsonResponse({'results': []})

    products = Product.objects.filter(
        is_active=True,
        quantity__gt=0,
    ).filter(
        models.Q(name__icontains=q) | models.Q(sku__icontains=q)
    )[:10]

    results = [{
        'id':    p.id,
        'name':  p.name,
        'sku':   p.sku or '',
        'price': str(p.price),
        'quantity': p.quantity,
        'image': p.image.url if p.image else '',
    } for p in products]

    return JsonResponse({'results': results})


@cashier_or_admin_required
@require_GET
def product_detail(request, pk):
    """Return single product data for POS cart."""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    return JsonResponse({
        'id':    product.id,
        'name':  product.name,
        'price': str(product.price),
        'quantity': product.quantity,
        'image': product.image.url if product.image else '',
    })
