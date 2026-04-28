from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from products.models import Product
from .models import StockMovement


@login_required
def stock_overview(request):
    products = Product.objects.filter(is_active=True).order_by('quantity')

    # tag stock level on each product
    for p in products:
        if p.quantity == 0:
            p.stock_status = 'out'
        elif p.quantity <= 5:
            p.stock_status = 'low'
        else:
            p.stock_status = 'ok'

    out_of_stock = [p for p in products if p.stock_status == 'out']
    low_stock = [p for p in products if p.stock_status == 'low']

    return render(request, 'inventory/overview.html', {
        'products':      products,
        'out_of_stock':  out_of_stock,
        'low_stock':     low_stock,
        'total_products': products.count(),
    })


@login_required
def stock_log(request):
    movements = StockMovement.objects.select_related('product',
                                                     'created_by').all()

    product_filter = request.GET.get('product')
    type_filter = request.GET.get('type')

    if product_filter:
        movements = movements.filter(product__id=product_filter)
    if type_filter:
        movements = movements.filter(movement_type=type_filter)

    products = Product.objects.filter(is_active=True)

    return render(request, 'inventory/log.html', {
        'movements':      movements[:200],
        'products':       products,
        'movement_types': StockMovement.MOVEMENT_TYPES,
        'product_filter': product_filter,
        'type_filter':    type_filter,
    })


@login_required
def restock_product(request, pk):
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages

    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 0))
        note = request.POST.get('note', '')

        if qty > 0:
            qty_before = product.quantity
            product.quantity += qty
            product.save(update_fields=['quantity'])

            StockMovement.objects.create(
                product=product,
                movement_type='restock',
                quantity=+qty,
                quantity_before=qty_before,
                quantity_after=product.quantity,
                note=note,
                created_by=request.user,
            )
            messages.success(request, f'{qty} units added to'
                             f'"{product.name}".')
        else:
            messages.error(request, 'Quantity must be greater than zero.')

    return redirect('inventory:overview')
