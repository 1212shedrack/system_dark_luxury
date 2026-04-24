from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password,  name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password,
         name='reset_password'),
    path('dashboard/admin/', views.admin_dashboard,  name='admin_dashboard'),
    path('dashboard/cashier/', views.cashier_dashboard,
         name='cashier_dashboard'),
    path('dashboard/customer/', views.customer_dashboard,
         name='customer_dashboard'),
]
