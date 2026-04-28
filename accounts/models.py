from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('cashier', 'Cashier'),
        ('customer', 'Customer'),
    )

    role = models.CharField(max_length=20,
                            choices=ROLE_CHOICES, default='customer')
    staff_number = models.CharField(max_length=20,
                                    unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

# from django.conf import settings


class ShopSettings(models.Model):
    shop_name = models.CharField(max_length=100, default='ShopOS')
    shop_address = models.TextField(blank=True, default='')
    shop_phone = models.CharField(max_length=20, blank=True, default='')
    currency = models.CharField(max_length=10, default='TZS')
    receipt_footer = models.TextField(blank=True,
                                      default='Thank you for your purchase!')
    logo = models.ImageField(upload_to='settings/', blank=True, null=True)
    low_stock_alert = models.PositiveIntegerField(default=5)
    items_per_page = models.PositiveIntegerField(default=20)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Shop Settings'

    def __str__(self):
        return self.shop_name

    @classmethod
    def get(cls):
        """Always returns the single settings row."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
