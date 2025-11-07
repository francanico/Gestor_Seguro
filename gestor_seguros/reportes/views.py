import csv
from django.db import models
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count,Q
from django.db.models.functions import TruncMonth
from datetime import datetime
from polizas.models import Poliza, Cliente

@login_required
def reportes_dashboard(request):
    user = request.user
    
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    
    # Queryset base para los datos del período (KPIs y gráfico de barras)
    polizas_query_periodo = Poliza.objects.filter(usuario=user)
    if fecha_inicio_str:
        polizas_query_periodo = polizas_query_periodo.filter(fecha_emision__gte=fecha_inicio_str)
    if fecha_fin_str:
        polizas_query_periodo = polizas_query_periodo.filter(fecha_emision__lte=fecha_fin_str)

    # 1. Producción por Mes (para gráfico de barras)
    produccion_por_mes = list(polizas_query_periodo.filter(
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
    
    # 3. Cartera por Ramo (para gráfico de dona) - Se calcula sobre TODA la cartera, no solo el período
    cartera_por_ramo = list(Poliza.objects.filter(usuario=user).values('ramo_tipo_seguro').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad'))
    
    # 3.1 Prima por aseguradora (para gráfico de dona) 
    produccion_por_aseguradora = list(
        polizas_query_periodo.filter(aseguradora__isnull=False)
        .values('aseguradora__nombre')
        .annotate(total_prima=Sum('prima_total_anual'))
        .order_by('-total_prima')
    )

    # 4. KPIs
    agregados_kpi = polizas_query_periodo.aggregate(
        total_primas=Sum('prima_total_anual', default=0),
        total_polizas=Count('id')
    )

    context = {
        'produccion_por_mes': produccion_por_mes,
        'cartera_por_ramo': cartera_por_ramo,
        'comisiones': comisiones,
        'total_primas': agregados_kpi.get('total_primas'),
        'total_polizas_periodo': agregados_kpi.get('total_polizas'),
        'fecha_inicio': fecha_inicio_str,
        'fecha_fin': fecha_fin_str,
        'titulo_pagina': 'Reportes de Agencia',
        'produccion_por_aseguradora': produccion_por_aseguradora,
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
        'Nro. Poliza',
        'Cliente',
        'Documento Cliente',
        'Email Cliente',
        'Telefono Cliente',
        'Aseguradora',
        'Ramo',
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
            poliza.numero_poliza,
            poliza.cliente.nombre_completo,
            f"{poliza.cliente.get_tipo_documento_display()}-{poliza.cliente.numero_documento}",
            poliza.cliente.email,
            poliza.cliente.telefono_principal,
            poliza.aseguradora.nombre if poliza.aseguradora else 'N/A',
            poliza.ramo_tipo_seguro,
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