# polizas/filters.py
import django_filters
from .models import Cliente
from django import forms
from django.db import models


class ClienteFilter(django_filters.FilterSet):
    nombre_o_doc = django_filters.CharFilter(
        method='filtro_nombre_o_doc', 
        label="Buscar Cliente",
        widget=forms.TextInput(attrs={'placeholder': 'Nombre o Cédula/RIF'})
    )

    class Meta:
        model = Cliente
        fields = [] # No necesitamos más filtros automáticos por ahora

    def filtro_nombre_o_doc(self, queryset, name, value):
        return queryset.filter(
            models.Q(nombre_completo__icontains=value) | 
            models.Q(numero_documento__icontains=value)
        )
