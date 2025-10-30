from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.reportes_dashboard, name='dashboard_reportes'),
    path('exportar/polizas/', views.exportar_polizas_csv, name='exportar_polizas_csv'),
]