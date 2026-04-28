from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.stock_overview, name='overview'),
    path('log/', views.stock_log, name='log'),
    path('restock/<int:pk>/', views.restock_product, name='restock'),
]
