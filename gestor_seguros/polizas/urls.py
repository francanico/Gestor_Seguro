# polizas/urls.py
from django.urls import path
from . import views

app_name = 'polizas' # Namespace para las URLs

urlpatterns = [
    path('', views.PolizaListView.as_view(), name='lista_polizas'),
    path('<int:pk>/', views.PolizaDetailView.as_view(), name='detalle_poliza'),
    path('nueva/', views.PolizaCreateView.as_view(), name='crear_poliza'),
    path('<int:pk>/editar/', views.PolizaUpdateView.as_view(), name='editar_poliza'),
    path('<int:pk>/eliminar/', views.PolizaDeleteView.as_view(), name='eliminar_poliza'),
    path('<int:pk>/renovar/', views.renovar_poliza, name='renovar_poliza'),
    path('pago/<int:pk>/eliminar/', views.eliminar_pago_cuota, name='eliminar_pago_cuota'),
    path('<int:pk>/registrar_pago_rapido/', views.registrar_pago_rapido, name='registrar_pago_rapido'),
    path('api/tasa-bcv/', views.obtener_tasa_bcv_api, name='api_tasa_bcv'),


    # URLs para Aseguradoras
    path('aseguradoras/', views.AseguradoraListView.as_view(), name='lista_aseguradoras'),
    path('aseguradoras/nueva/', views.AseguradoraCreateView.as_view(), name='crear_aseguradora'),
    path('aseguradoras/<int:pk>/editar/', views.AseguradoraUpdateView.as_view(), name='editar_aseguradora'),
    path('aseguradoras/<int:pk>/eliminar/', views.AseguradoraDeleteView.as_view(), name='eliminar_aseguradora'),

    # Dashboard (si lo moviste aquí, si no, va en el urls.py principal)
    # path('dashboard/', views.dashboard_view, name='dashboard'), # Si se define en polizas/views.py

    # URLs para Siniestros
    path('siniestro/<int:pk>/', views.SiniestroDetailView.as_view(), name='detalle_siniestro'),
    path('poliza/<int:poliza_pk>/siniestro/nuevo/', views.SiniestroCreateView.as_view(), name='crear_siniestro'),
    path('siniestro/<int:pk>/editar/', views.SiniestroUpdateView.as_view(), name='editar_siniestro'),
    path('siniestro/<int:pk>/eliminar/', views.SiniestroDeleteView.as_view(), name='eliminar_siniestro'),

]