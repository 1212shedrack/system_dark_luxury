from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import Product
import os


@receiver(post_delete, sender=Product)
def delete_image_on_product_delete(sender, instance, **kwargs):
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(pre_save, sender=Product)
def delete_old_image_on_product_update(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Product.objects.get(pk=instance.pk)
    except Product.DoesNotExist:
        return
    if old.image and old.image != instance.image:
        if os.path.isfile(old.image.path):
            os.remove(old.image.path)
