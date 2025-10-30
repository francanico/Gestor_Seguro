from django.urls import path
from . import views

app_name = 'documentos'

urlpatterns = [
    path('subir/<int:content_type_id>/<int:object_id>/', views.subir_documento, name='subir_documento'),
    path('<int:pk>/eliminar/', views.eliminar_documento, name='eliminar_documento'),
]