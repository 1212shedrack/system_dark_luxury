from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):

    UNIT_CHOICES = [
        ('piece',  'Piece'),
        ('kg',     'Kilogram (kg)'),
        ('g',      'Gram (g)'),
        ('ltr',    'Litre (ltr)'),
        ('ml',     'Millilitre (ml)'),
        ('pkt',    'Packet (pkt)'),
        ('box',    'Box'),
        ('dozen',  'Dozen'),
        ('bottle', 'Bottle'),
    ]

    id = models.AutoField(primary_key=True)
    name  = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='piece')
    allow_decimal = models.BooleanField(default=False,
                    help_text='Allow selling fractional quantities e.g. 0.5 kg')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.unit})"

