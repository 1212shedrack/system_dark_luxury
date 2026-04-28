from django.db.models.signals import post_save
from django.dispatch import receiver
from POS.models import Sale
from orders.models import Order
from .models import StockMovement


@receiver(post_save, sender=Sale)
def handle_sale_stock(sender, instance, created, **kwargs):
    # Stock reduction and logging handled directly in pos/views.py
    # to avoid double reduction. This signal only handles edge cases.
    pass

    # On refund — restore stock
    if not created and instance.status == Sale.STATUS_REFUNDED:
        # only restore if not already restored
        already_refunded = StockMovement.objects.filter(
            reference=instance.sale_number,
            movement_type='refund'
        ).exists()

        if not already_refunded:
            for item in instance.items.all():
                product = item.product
                qty_before = product.quantity
                product.quantity += item.quantity
                product.save(update_fields=['quantity'])

                StockMovement.objects.create(
                    product=product,
                    movement_type='refund',
                    quantity=+item.quantity,
                    quantity_before=qty_before,
                    quantity_after=product.quantity,
                    reference=instance.sale_number,
                    created_by=instance.cashier,
                )


@receiver(post_save, sender=Order)
def handle_order_stock(sender, instance, created, **kwargs):
    # Reduce stock when order moves to confirmed
    if not created and instance.status == 'confirmed':
        already_reduced = StockMovement.objects.filter(
            reference=f'ORD-{instance.id}',
            movement_type='order'
        ).exists()

        if not already_reduced:
            for item in instance.order_items.all():
                product = item.product
                qty_before = product.quantity
                product.quantity -= item.quantity
                product.quantity = max(0, product.quantity)
                product.save(update_fields=['quantity'])

                StockMovement.objects.create(
                    product=product,
                    movement_type='order',
                    quantity=-item.quantity,
                    quantity_before=qty_before,
                    quantity_after=product.quantity,
                    reference=f'ORD-{instance.id}',
                    created_by=instance.customer,
                )

    # Restore stock if order cancelled
    if not created and instance.status == 'cancelled':
        already_restored = StockMovement.objects.filter(
            reference=f'ORD-{instance.id}',
            movement_type='refund'
        ).exists()

        if not already_restored:
            for item in instance.order_items.all():
                product = item.product
                qty_before = product.quantity
                product.quantity += item.quantity
                product.save(update_fields=['quantity'])

                StockMovement.objects.create(
                    product=product,
                    movement_type='refund',
                    quantity=+item.quantity,
                    quantity_before=qty_before,
                    quantity_after=product.quantity,
                    reference=f'ORD-{instance.id}',
                    created_by=instance.customer,
                )
