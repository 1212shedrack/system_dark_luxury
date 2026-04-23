from django.urls import path
from . import views

urlpatterns = [

    path('register/', views.register, name='register'),
    # path('login/', views.login_view, name='login'),
    path('login/', views.customer_login, name='customer_login'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('cashier-login/', views.cashier_login, name='cashier_login'),
    path('admin-dashboard/', views.admin_dashboard,
         name='admin_dashboard'),
    path('cashier-dashboard/', views.cashier_dashboard,
         name='cashier_dashboard'),
    path('customer-dashboard/', views.customer_dashboard,
         name='customer_dashboard'),
    path('logout/', views.logout_view, name='logout'),

]
