from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product
from .cart import Cart
# from cart.models import Cart, CartItem
# from orders.models import Order, OrderItem


def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    cart.add(product=product)

    return redirect(request.META.get('HTTP_REFERER', 'products:product_list'))


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/cart_detail.html', {'cart': cart})


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    cart.remove(product)
    return redirect('cart:cart_detail')


def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    quantity = int(request.POST.get('quantity'))
    cart.update(product, quantity)

    return redirect('cart:cart_detail')
