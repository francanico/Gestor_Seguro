import csv
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
from polizas.models import Poliza, Aseguradora
from clientes.models import Cliente
from django.utils import timezone


@login_required
def reportes_dashboard(request):
    user = request.user
    
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    filtro_rapido = request.GET.get('filtro_rapido')
    
    hoy = timezone.now().date()
    
    # Lógica de botones rápidos
    if filtro_rapido == 'este_mes':
        fecha_inicio_str = hoy.replace(day=1).strftime('%Y-%m-%d')
        fecha_fin_str = hoy.strftime('%Y-%m-%d')
    elif filtro_rapido == 'mes_pasado':
        primer_dia_este_mes = hoy.replace(day=1)
        ultimo_dia_mes_pasado = primer_dia_este_mes - timedelta(days=1)
        primer_dia_mes_pasado = ultimo_dia_mes_pasado.replace(day=1)
        fecha_inicio_str = primer_dia_mes_pasado.strftime('%Y-%m-%d')
        fecha_fin_str = ultimo_dia_mes_pasado.strftime('%Y-%m-%d')
    elif filtro_rapido == 'este_anio':
        fecha_inicio_str = hoy.replace(month=1, day=1).strftime('%Y-%m-%d')
        fecha_fin_str = hoy.strftime('%Y-%m-%d')
    
    # Queryset base para TODAS las pólizas del usuario
    polizas_base = Poliza.objects.filter(usuario=user)
    
    # Queryset para los datos que SÍ dependen del período (KPIs y gráfico de barras)
    polizas_query_periodo = polizas_base
    if fecha_inicio_str:
        polizas_query_periodo = polizas_query_periodo.filter(fecha_emision__gte=fecha_inicio_str)
    if fecha_fin_str:
        # Añadimos +1 día al filtro 'lte' si usamos fechas, para incluir el día completo
        # Pero como el input es 'date', no es necesario.
        polizas_query_periodo = polizas_query_periodo.filter(fecha_emision__lte=fecha_fin_str)

    # Condición para pólizas activas (en vigencia actualmente)
    condicion_activa = Q(fecha_inicio_vigencia__lte=hoy, fecha_fin_vigencia__gte=hoy)

    # 1. Producción por Mes (para gráfico de barras)
    produccion_por_mes = list(polizas_query_periodo.filter(
        condicion_activa,
        prima_total_anual__gt=0
    ).annotate(
        mes=TruncMonth('fecha_emision')
    ).values('mes').annotate(
        total_prima=Sum('prima_total_anual')
    ).order_by('mes'))

    # 2. Resumen de Comisiones (para KPI)
    comisiones = polizas_query_periodo.aggregate(
        cobradas=Sum('comision_monto', filter=Q(comision_cobrada=True), default=0),
        pendientes=Sum('comision_monto', filter=Q(comision_cobrada=False), default=0),
    )
    
    # 3. Cartera por Ramo (para gráfico de dona)
    cartera_por_ramo = list(polizas_base.filter(condicion_activa).values('ramo_tipo_seguro').annotate(
        cantidad=Count('id'),
        total_prima=Sum('prima_total_anual')
    ).order_by('-cantidad'))
    
    # 4. Cartera por Aseguradora (NUEVO GRÁFICO)
    cartera_por_aseguradora = list(polizas_base.filter(condicion_activa).annotate(
        nombre_aseguradora=models.F('aseguradora__nombre')
    ).values('nombre_aseguradora').annotate(
        cantidad=Count('id'),
        total_prima=Sum('prima_total_anual')
    ).order_by('-cantidad'))

    # 5. KPIs
    agregados_kpi = polizas_query_periodo.aggregate(
        total_primas=Sum('prima_total_anual', filter=condicion_activa, default=0),
        total_polizas=Count('id')
    )

    context = {
        # --- Datos para los Gráficos ---
        'produccion_por_mes': produccion_por_mes,
        'cartera_por_ramo': cartera_por_ramo,
        'cartera_por_aseguradora': cartera_por_aseguradora, # Nuevo dato
        
        # --- Datos para KPIs y Filtros ---
        'comisiones': comisiones,
        'total_primas': agregados_kpi.get('total_primas'),
        'total_polizas_periodo': agregados_kpi.get('total_polizas'),
        'fecha_inicio': fecha_inicio_str,
        'fecha_fin': fecha_fin_str,
        'titulo_pagina': 'Reportes de Agencia',

    }
    return render(request, 'reportes/reportes_dashboard.html', context)


# --- VISTA DE EXPORTACIÓN ---
@login_required
def exportar_polizas_csv(request):
    # --- 1. Definir el nombre del archivo y la respuesta HTTP ---
    filename = f'reporte_polizas_{datetime.now().strftime("%Y-%m-%d")}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # --- 2. Añadir BOM para compatibilidad con Excel ---
    # BOM (Byte Order Mark) le dice a Excel que el archivo es UTF-8
    response.write('\ufeff'.encode('utf8'))

    # --- 3. Obtener los filtros de fecha de la URL (si existen) ---
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')

    # --- 4. Construir el queryset filtrado ---
    polizas_query = Poliza.objects.filter(usuario=request.user).select_related('cliente', 'aseguradora').order_by('cliente__nombre_completo', 'fecha_fin_vigencia')

    if fecha_inicio_str:
        polizas_query = polizas_query.filter(fecha_emision__gte=fecha_inicio_str)
    if fecha_fin_str:
        polizas_query = polizas_query.filter(fecha_emision__lte=fecha_fin_str)

    # --- 5. Definir las cabeceras del CSV (más claras y en español) ---
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'ID Poliza',
        'Nro. Poliza',
        'Cliente',
        'Documento Cliente',
        'Email Cliente',
        'Telefono Cliente',
        'Aseguradora',
        'Ramo',
        'Bien Asegurado (Placa)',
        'Fecha Emision',
        'Fecha Inicio Vigencia',
        'Fecha Fin Vigencia',
        'Prima Total Anual',
        'Monto Comision',
        'Comision Cobrada',
        'Estado de la Poliza',
        'Frecuencia de Pago',
    ])

    # --- 6. Escribir los datos de cada póliza en el CSV ---
    for poliza in polizas_query:
        writer.writerow([
            poliza.id,
            poliza.numero_poliza,
            poliza.cliente.nombre_completo,
            f"{poliza.cliente.get_tipo_documento_display()}-{poliza.cliente.numero_documento}",
            poliza.cliente.email,
            poliza.cliente.telefono_principal,
            poliza.aseguradora.nombre if poliza.aseguradora else 'N/A',
            poliza.ramo_tipo_seguro,
            poliza.descripcion_bien_asegurado,
            poliza.fecha_emision.strftime('%d/%m/%Y'),
            poliza.fecha_inicio_vigencia.strftime('%d/%m/%Y'),
            poliza.fecha_fin_vigencia.strftime('%d/%m/%Y'),
            poliza.prima_total_anual,
            poliza.comision_monto,
            'Si' if poliza.comision_cobrada else 'No',
            poliza.get_estado_poliza_display(),
            poliza.get_frecuencia_pago_display(),
        ])
        
    return response


# -----------------------------------------------------------------------
# REPORTE AVANZADO CON FILTROS MÚCTIPLES
# -----------------------------------------------------------------------

def _aplicar_filtros_avanzados(queryset, params, user):
    """Aplica todos los filtros avanzados sobre un queryset base de pólizas."""
    cliente_id   = params.get('cliente')
    aseguradora_id = params.get('aseguradora')
    ramo         = params.get('ramo')
    estado       = params.get('estado')
    vencimiento  = params.get('vencimiento')   # dias: 30, 60, 90, 'vencidas'
    fecha_inicio = params.get('fecha_inicio_vigencia')
    fecha_fin    = params.get('fecha_fin_vigencia')

    if cliente_id:
        queryset = queryset.filter(cliente_id=cliente_id)
    if aseguradora_id:
        queryset = queryset.filter(aseguradora_id=aseguradora_id)
    if ramo:
        queryset = queryset.filter(ramo_tipo_seguro__icontains=ramo)
    if estado:
        queryset = queryset.filter(estado_poliza=estado)
    if fecha_inicio:
        queryset = queryset.filter(fecha_fin_vigencia__gte=fecha_inicio)
    if fecha_fin:
        queryset = queryset.filter(fecha_fin_vigencia__lte=fecha_fin)
    if vencimiento:
        hoy = timezone.now().date()
        if vencimiento == 'vencidas':
            queryset = queryset.filter(fecha_fin_vigencia__lt=hoy)
        else:
            try:
                dias = int(vencimiento)
                limite = hoy + timedelta(days=dias)
                queryset = queryset.filter(fecha_fin_vigencia__gte=hoy, fecha_fin_vigencia__lte=limite)
            except ValueError:
                pass
    return queryset


@login_required
def reporte_avanzado(request):
    user = request.user

    # Listas para los selectores
    clientes       = Cliente.objects.filter(usuario=user).order_by('nombre_completo')
    aseguradoras   = Aseguradora.objects.filter(usuario=user).order_by('nombre')
    ramos          = Poliza.objects.filter(usuario=user).values_list(
                        'ramo_tipo_seguro', flat=True).distinct().order_by('ramo_tipo_seguro')
    estados        = Poliza.ESTADO_POLIZA_CHOICES

    polizas = None
    total_registros = 0
    total_prima = 0
    hay_busqueda = any(request.GET.get(k) for k in [
        'cliente', 'aseguradora', 'ramo', 'estado',
        'vencimiento', 'fecha_inicio_vigencia', 'fecha_fin_vigencia'
    ])

    if hay_busqueda:
        base = Poliza.objects.filter(usuario=user).select_related('cliente', 'aseguradora').order_by('fecha_fin_vigencia')
        polizas = _aplicar_filtros_avanzados(base, request.GET, user)
        agg = polizas.aggregate(total=Count('id'), prima=Sum('prima_total_anual'))
        total_registros = agg['total']
        total_prima = agg['prima'] or 0

    context = {
        'titulo_pagina': 'Reporte Avanzado',
        'clientes':     clientes,
        'aseguradoras': aseguradoras,
        'ramos':        ramos,
        'estados':      estados,
        'polizas':      polizas,
        'total_registros': total_registros,
        'total_prima':  total_prima,
        'hay_busqueda': hay_busqueda,
        'params':       request.GET,   # para repoblar el form
    }
    return render(request, 'reportes/reporte_avanzado.html', context)


@login_required
def exportar_reporte_avanzado_csv(request):
    user = request.user
    base = Poliza.objects.filter(usuario=user).select_related('cliente', 'aseguradora').order_by('fecha_fin_vigencia')
    polizas = _aplicar_filtros_avanzados(base, request.GET, user)

    filename = f'reporte_avanzado_{datetime.now().strftime("%Y-%m-%d")}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff'.encode('utf8'))   # BOM para Excel

    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        'Nro. Póliza', 'Cliente', 'Documento Cliente', 'Email Cliente', 'Teléfono Cliente',
        'Aseguradora', 'Ramo', 'Bien Asegurado',
        'Fecha Inicio Vigencia', 'Fecha Fin Vigencia', 'Días para Vencer',
        'Prima Total Anual', 'Frecuencia Pago', 'Próx. Cuota / Monto',
    ])

    hoy = timezone.now().date()
    for p in polizas:
        dias = (p.fecha_fin_vigencia - hoy).days if p.fecha_fin_vigencia else ''
        proxima_cuota = p.proxima_cuota_pendiente
        if proxima_cuota:
            proximo_pago = f"{proxima_cuota.fecha_vencimiento_cuota.strftime('%d/%m/%Y')} - ${proxima_cuota.monto_cuota}"
        else:
            proximo_pago = "Al día"
            if p.proxima_fecha_renovacion_calculada:
                proximo_pago += f" (Renov: {p.proxima_fecha_renovacion_calculada.strftime('%d/%m/%Y')})"
        writer.writerow([
            p.numero_poliza,
            p.cliente.nombre_completo,
            f"{p.cliente.get_tipo_documento_display()}-{p.cliente.numero_documento}",
            p.cliente.email or '',
            p.cliente.telefono_principal or '',
            p.aseguradora.nombre if p.aseguradora else '',
            p.ramo_tipo_seguro,
            p.descripcion_bien_asegurado or '',
            p.fecha_inicio_vigencia.strftime('%d/%m/%Y'),
            p.fecha_fin_vigencia.strftime('%d/%m/%Y'),
            dias,
            p.prima_total_anual,
            p.get_frecuencia_pago_display(),
            proximo_pago,
        ])

    return response