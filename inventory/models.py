from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()


class StockMovement(models.Model):
    MOVEMENT_TYPES = [
        ('sale',        'POS Sale'),
        ('order',       'Online Order'),
        ('refund',      'Refund'),
        ('restock',     'Restock'),
        ('adjustment',  'Manual Adjustment'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    # negative = stock out, positive = stock in
    quantity = models.IntegerField()
    quantity_before = models.IntegerField()
    quantity_after = models.IntegerField()
    # sale number or order id
    reference = models.CharField(max_length=50, blank=True)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(User,
                                   on_delete=models.SET_NULL,
                                   null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        direction = 'out' if self.quantity < 0 else 'in'
        return (
            f"{self.product.name} — "
            f"{abs(self.quantity)} {direction} "
            f"({self.movement_type})"
             )
