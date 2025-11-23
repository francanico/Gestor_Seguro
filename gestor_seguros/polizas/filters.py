# polizas/filters.py
import django_filters
from .models import Poliza
from django import forms
from django.db import models

class PolizaFilter(django_filters.FilterSet):
    # Campo de búsqueda de texto libre que busca en varios campos
    q = django_filters.CharFilter(
        method='filtro_general', 
        label="Buscar",
        widget=forms.TextInput(attrs={'placeholder': 'Nro. Póliza, Cliente, Placa'})
    )

    class Meta:
        model = Poliza
        # Campos por los que se puede filtrar con desplegables
        fields = {
            'aseguradora': ['exact'],
            'ramo_tipo_seguro': ['icontains'],
            'estado_poliza': ['exact'],
        }

    def filtro_general(self, queryset, name, value):
        # Esta función define cómo funciona la búsqueda de texto libre 'q'
        return queryset.filter(
            models.Q(numero_poliza__icontains=value) |
            models.Q(cliente__nombre_completo__icontains=value) |
            models.Q(aseguradora__nombre__icontains=value) |
            models.Q(descripcion_bien_asegurado__icontains=value)
        )