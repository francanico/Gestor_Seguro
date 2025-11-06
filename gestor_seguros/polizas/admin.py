# polizas/admin.py
from django.contrib import admin
from .models import Poliza, Aseguradora,PagoCuota


# --- REGISTRA EL NUEVO MODELO DE PAGOS ---
@admin.register(PagoCuota)
class PagoCuotaAdmin(admin.ModelAdmin):
    # Usamos los nombres de campo NUEVOS
    list_display = ('poliza', 'fecha_vencimiento_cuota', 'monto_cuota', 'estado', 'fecha_de_pago_realizado')
    list_filter = ('estado', 'fecha_vencimiento_cuota', 'poliza__aseguradora')
    search_fields = ('poliza__numero_poliza', 'poliza__cliente__nombre_completo')
    list_editable = ('estado', 'fecha_de_pago_realizado') # Permite editar estos campos desde la lista
    autocomplete_fields = ['poliza']

# --- OPCIONAL: MOSTRAR PAGOS EN LA VISTA DE LA PÓLIZA ---
class PagoCuotaInline(admin.TabularInline):
    model = PagoCuota
    extra = 0 # No mostrar formularios vacíos para añadir
    
    # Usamos los nombres de campo NUEVOS
    readonly_fields = ('fecha_vencimiento_cuota', 'monto_cuota', 'estado', 'fecha_de_pago_realizado')
    
    # Mostramos estos campos en el inline
    fields = ('fecha_vencimiento_cuota', 'monto_cuota', 'estado', 'fecha_de_pago_realizado')
    
    can_delete = False # No permitir borrar cuotas desde aquí
    
    def has_add_permission(self, request, obj=None):
        return False # No permitir añadir cuotas manualmente desde el admin

@admin.register(Aseguradora)
class AseguradoraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rif', 'contacto_nombre', 'contacto_email')
    search_fields = ('nombre', 'rif')

@admin.register(Poliza)
class PolizaAdmin(admin.ModelAdmin):
    list_display = (
        'numero_poliza', 'cliente', 'aseguradora', 'ramo_tipo_seguro',
        'fecha_inicio_vigencia', 'fecha_fin_vigencia', 'estado_renovacion',
        'prima_total_anual', 'comision_monto', 'comision_cobrada', 'estado_poliza'
    )
    
    search_fields = (
        'numero_poliza', 'cliente__nombre_completo', 'cliente__numero_documento',
        'aseguradora__nombre', 'ramo_tipo_seguro'
    )
    list_filter = (
        'estado_poliza', 'frecuencia_pago', 'comision_cobrada',
        'aseguradora', 'fecha_fin_vigencia', 'fecha_inicio_vigencia'
    )
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'dias_para_renovar', 'estado_renovacion')
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
            'fields': ('comision_monto', 'comision_cobrada', 'fecha_cobro_comision')
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

    inlines = [PagoCuotaInline] # Agrega la sección de pagos en la vista de la póliza

    def get_queryset(self, request):
        # Optimizar consulta para evitar N+1
        return super().get_queryset(request).select_related('cliente', 'aseguradora')

