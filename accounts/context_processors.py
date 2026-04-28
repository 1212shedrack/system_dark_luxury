from .models import ShopSettings


def shop_settings(request):
    """Injects shop_settings into every template automatically."""
    try:
        settings = ShopSettings.get()
    except Exception:
        settings = None
    return {'shop_settings': settings}
