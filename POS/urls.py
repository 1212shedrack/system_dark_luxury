from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('screen/', views.pos_screen, name='screen'),
    path('process/', views.process_sale, name='process'),
    path('receipt/<int:sale_id>/', views.receipt, name='receipt'),
    path('history/', views.sale_history, name='history'),
    path('refund/<int:sale_id>/', views.refund_sale, name='refund'),

    # AJAX endpoints
    path('api/search/', views.product_search, name='api_search'),
    path('api/product/<int:pk>/', views.product_detail, name='api_product'),
]
