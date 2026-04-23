# cart/context_processors.py
def cart_total(request):
    cart = request.session.get('cart', {})
    total_items = sum(item['quantity'] for item in cart.values())
    return {'cart_total': total_items}
