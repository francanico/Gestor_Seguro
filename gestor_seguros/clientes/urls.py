# clientes/urls.py
from django.urls import path
from . import views

app_name = 'clientes' # Namespace para las URLs

urlpatterns = [
    path('', views.ClienteListView.as_view(), name='lista_clientes'),
    path('<int:pk>/', views.ClienteDetailView.as_view(), name='detalle_cliente'),
    path('nuevo/', views.ClienteCreateView.as_view(), name='crear_cliente'),
    path('<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='editar_cliente'),
    path('<int:pk>/eliminar/', views.ClienteDeleteView.as_view(), name='eliminar_cliente'),
]