# account/signals.py

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from cart.models import Cart, CartItem
from products.models import Product


@receiver(user_logged_in)
def save_session_cart_to_db(sender, request, user, **kwargs):
    session_cart = request.session.get('cart', {})
    if not session_cart:
        return

    cart, created = Cart.objects.get_or_create(user=user)

    for product_id, item_data in session_cart.items():
        try:
            product = Product.objects.get(id=product_id)
            cart_item, _ = CartItem.objects.get_or_create(cart=cart,
                                                          product=product)
            cart_item.quantity = item_data['quantity']
            cart_item.save()
        except Product.DoesNotExist:
            pass

    # clear session cart after saving
    request.session['cart'] = {}
