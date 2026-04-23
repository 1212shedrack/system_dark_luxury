# orders/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView

from .models import Order, OrderItem
from cart.cart import Cart
from accounts.mixins import CashierOrAdminMixin


# ══════════════════════════════════════
#  CUSTOMER — place order from cart
# ══════════════════════════════════════

@login_required
def place_order(request):
    cart = Cart(request)

    if len(cart) == 0:
        return redirect('cart:cart_detail')  # empty cart, go back

    if request.method == 'POST':
        # create the order
        order = Order.objects.create(
            customer=request.user,
            created_by=request.user,
            status='pending',
        )

        # save each cart item as an order item
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price'],
            )

        # clear the cart after ordering
        cart.clear()

        return redirect('orders:order_confirmation', pk=order.pk)

    # GET — show order summary before confirming
    return render(request, 'orders/order_summary.html', {'cart': cart})


# ══════════════════════════════════════
#  CUSTOMER — their own orders
# ══════════════════════════════════════

@login_required
def customer_order_list(request):
    orders = Order.objects.filter(customer=request.user) \
                          .prefetch_related('order_items__product') \
                          .order_by('-created_at')
    return render(request, 'orders/customer_order_list.html',
                  {'orders': orders})


@login_required
def order_confirmation(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})


@login_required
def order_summary(request, pk):
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    return render(request, 'orders/order_summary.html', {'order': order})


@login_required
def cancel_order(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(Order, pk=order_id, customer=request.user)

        if order.status == 'pending':
            order.status = 'cancelled'
            order.save()

    return redirect('orders:customer_order_list')

# ══════════════════════════════════════
#  CASHIER / ADMIN — all orders
# ══════════════════════════════════════


class OrderListView(CashierOrAdminMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        qs = Order.objects.select_related('customer', 'created_by') \
                          .prefetch_related('order_items__product') \
                          .order_by('-created_at')

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        context['total_count'] = Order.objects.count()
        context['pending_count'] = Order.objects.filter(
            status='pending').count()
        context['completed_count'] = Order.objects.filter(
            status='completed').count()
        context['cancelled_count'] = Order.objects.filter(
            status='cancelled').count()
        context['processing_count'] = Order.objects.filter(
            status='processing').count()
        return context


class OrderDetailView(CashierOrAdminMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        status = request.POST.get('status')

        if status in dict(Order.STATUS_CHOICES):
            order.status = status
            order.save()

        return redirect('orders:order_detail', pk=order.pk)
