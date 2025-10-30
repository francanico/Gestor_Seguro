# gestor_seguros/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Importa la vista de página de inicio (ajusta la ruta si la pusiste en otro lado)
from cuentas.views import pagina_inicio
# Importa la vista del dashboard para la redirección después del login
from polizas.views import dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # Página de Inicio Pública
    path('', pagina_inicio, name='pagina_inicio'), # <--- PÁGINA DE INICIO

    # Apps con contenido protegido
    path('dashboard/', dashboard_view, name='dashboard'), # Dashboard ahora tiene su propia URL
    path('clientes/', include('clientes.urls', namespace='clientes')),
    path('polizas/', include('polizas.urls', namespace='polizas')), # El dashboard de polizas está en polizas/views.py

    # App de Cuentas (registro, etc.)
    path('cuentas/', include('cuentas.urls', namespace='cuentas')),

    # Autenticación (usando las vistas de Django)
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True # Si está logueado, lo manda a LOGIN_REDIRECT_URL
        ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        # next_page='pagina_inicio' # Redirige a la página de inicio pública después del logout
        ), name='logout'), # Por defecto, Django redirige a LOGIN_URL o a una página de "logout exitoso"

    # App de Reportes
    path('reportes/', include('reportes.urls', namespace='reportes')),

        # App de Documentos
    path('documentos/', include('documentos.urls', namespace='documentos')),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)