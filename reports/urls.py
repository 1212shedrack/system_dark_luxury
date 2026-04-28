from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_overview, name='overview'),
    path('export/', views.export_csv, name='export'),
]
