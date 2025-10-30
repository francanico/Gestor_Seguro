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
    
    polizas_query = Poliza.objects.filter(usuario=user)
    
    # Aplicamos el filtro de fecha SOLO al queryset base
    if fecha_inicio_str:
        polizas_query = polizas_query.filter(fecha_emision__gte=fecha_inicio_str)
    if fecha_fin_str:
        polizas_query = polizas_query.filter(fecha_emision__lte=fecha_fin_str)

    # 1. Reporte de Producción (Primas emitidas por mes)
    produccion_por_mes = polizas_query.annotate(
        mes=TruncMonth('fecha_emision')
    ).values('mes').annotate(
        total_prima=Sum('prima_total_anual')
    ).order_by('mes')

    # 2. Reporte de Comisiones (para el período filtrado)
    comisiones = polizas_query.aggregate(
        cobradas=Sum('comision_monto', filter=models.Q(comision_cobrada=True)),
        pendientes=Sum('comision_monto', filter=models.Q(comision_cobrada=False)),
    )
    
    # 3. Reporte de Cartera (Pólizas por Ramo - TOTAL, no filtrado por fecha)
    cartera_por_ramo_total = Poliza.objects.filter(usuario=user).values('ramo_tipo_seguro').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')

    # --- NUEVOS CÁLCULOS PARA KPIs ---
    # Suma total de primas en el período filtrado
    total_primas_periodo = polizas_query.aggregate(total=Sum('prima_total_anual'))['total']
    # Conteo de pólizas en el período filtrado
    total_polizas_periodo = polizas_query.count()

    context = {
        'produccion_por_mes': produccion_por_mes,
        'comisiones': comisiones,
        'cartera_por_ramo': cartera_por_ramo_total, # Usamos el total para el gráfico
        'total_primas': total_primas_periodo,      # Nuevo KPI
        'total_polizas_periodo': total_polizas_periodo, # Nuevo KPI
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
    writer = csv.writer(response)
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