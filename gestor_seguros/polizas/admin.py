# polizas/admin.py
from django.contrib import admin
from .models import Poliza, Aseguradora

@admin.register(Aseguradora)
class AseguradoraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nit', 'contacto_nombre', 'contacto_email')
    search_fields = ('nombre', 'nit')

@admin.register(Poliza)
class PolizaAdmin(admin.ModelAdmin):
    list_display = (
        'numero_poliza', 'cliente', 'aseguradora', 'ramo_tipo_seguro',
        'fecha_inicio_vigencia', 'fecha_fin_vigencia', 'estado_renovacion',
        'prima_total_anual', 'comision_porcentaje', 'comision_cobrada', 'estado_poliza'
    )
    search_fields = (
        'numero_poliza', 'cliente__nombre_completo', 'cliente__numero_documento',
        'aseguradora__nombre', 'ramo_tipo_seguro'
    )
    list_filter = (
        'estado_poliza', 'frecuencia_pago', 'comision_cobrada',
        'aseguradora', 'fecha_fin_vigencia', 'fecha_inicio_vigencia'
    )
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'monto_comision_calculado', 'dias_para_renovar', 'estado_renovacion')
    autocomplete_fields = ['cliente', 'aseguradora'] # Para una mejor selección de FKs

    fieldsets = (
        ("Información Principal", {
            'fields': ('cliente', 'aseguradora', 'numero_poliza', 'ramo_tipo_seguro', 'descripcion_bien_asegurado', 'estado_poliza')
        }),
        ("Vigencia y Pagos", {
            'fields': (('fecha_emision', 'fecha_inicio_vigencia', 'fecha_fin_vigencia'),
                    'prima_total_anual', 'frecuencia_pago', 'valor_cuota')
        }),
        ("Comisiones", {
            'fields': ('comision_porcentaje', 'monto_comision_calculado', 'comision_cobrada', 'fecha_cobro_comision')
        }),
        ("Recordatorios y Estado", {
            'fields': ('dias_para_renovar', 'estado_renovacion'),
        }),
        ("Documentos y Notas", {
            'fields': ('archivo_poliza', 'notas_poliza')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        # Optimizar consulta para evitar N+1
        return super().get_queryset(request).select_related('cliente', 'aseguradora')