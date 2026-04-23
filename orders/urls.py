# orders/urls.py

from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    # customer urls
    path('place/', views.place_order, name='place_order'),
    path('my-orders/', views.customer_order_list,  name='customer_order_list'),
    path('confirmation/<int:pk>/',
         views.order_confirmation, name='order_confirmation'),
    path("orders", views.cancel_order, name="cancel_order"),
    path("order-summary/<int:pk>/", views.order_summary, name="order_summary"),

    # cashier / admin urls
    path('all/', views.OrderListView.as_view(),   name='order_list'),
    path('all/<int:pk>/', views.OrderDetailView.as_view(),
         name='order_detail'),
]
