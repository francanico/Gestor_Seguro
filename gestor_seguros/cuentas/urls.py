# cuentas/urls.py
from django.urls import path
from . import views

app_name = 'cuentas'

urlpatterns = [
    path('registro/', views.registro_usuario, name='registro'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'), # <-- NUEVA URL
]