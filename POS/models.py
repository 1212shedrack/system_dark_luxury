from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from products.models import Product

User = get_user_model()


class Sale(models.Model):
    PAYMENT_CASH = 'cash'
    PAYMENT_MOBILE = 'mobile_money'
    PAYMENT_CARD = 'card'
    PAYMENT_CHOICES = [
        (PAYMENT_CASH,   'Cash'),
        (PAYMENT_MOBILE, 'Mobile Money'),
        (PAYMENT_CARD,   'Card'),
    ]

    STATUS_COMPLETED = 'completed'
    STATUS_REFUNDED = 'refunded'
    STATUS_CHOICES = [
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_REFUNDED,  'Refunded'),
    ]

    cashier = models.ForeignKey(User, on_delete=models.PROTECT,
                                related_name='sales')
    sale_number = models.CharField(max_length=20, unique=True, editable=False)
    payment_method = models.CharField(max_length=20,
                                      choices=PAYMENT_CHOICES,
                                      default=PAYMENT_CASH)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default=STATUS_COMPLETED)
    total_amount = models.DecimalField(max_digits=12,
                                       decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12,
                                      decimal_places=2, default=0)
    change_due = models.DecimalField(max_digits=12,
                                     decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sale {self.sale_number} — TZS {self.total_amount}"

    def save(self, *args, **kwargs):
        if not self.sale_number:
            self.sale_number = self._generate_sale_number()
        super().save(*args, **kwargs)

    def _generate_sale_number(self):
        today = timezone.now().strftime('%Y%m%d')
        count = Sale.objects.filter(created_at__date=timezone.now()
                                    .date()).count() + 1
        return f"POS-{today}-{count:04d}"

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE,
                             related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
