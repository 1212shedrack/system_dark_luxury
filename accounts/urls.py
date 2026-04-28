from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password,
         name='reset_password'),

    # Dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/cashier/', views.cashier_dashboard,
         name='cashier_dashboard'),
    path('dashboard/customer/', views.customer_dashboard,
         name='customer_dashboard'),

    # Manage cashiers
    path('cashiers/', views.cashier_list, name='cashier_list'),
    path('cashiers/add/', views.cashier_add, name='cashier_add'),
    path('cashiers/<int:pk>/edit/', views.cashier_edit, name='cashier_edit'),
    path('cashiers/<int:pk>/toggle/', views.cashier_toggle,
         name='cashier_toggle'),
    path('cashiers/<int:pk>/reset-password/', views.cashier_reset_password,
         name='cashier_reset_password'),

    # Manage customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/<int:pk>/detail/', views.customer_detail,
         name='customer_detail'),
    path('customers/<int:pk>/toggle/', views.customer_toggle,
         name='customer_toggle'),

    # Settings
    path('settings/', views.shop_settings_view, name='shop_settings'),
    path('settings/password/', views.change_password, name='change_password'),
]
