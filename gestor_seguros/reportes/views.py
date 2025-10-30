import csv
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from datetime import datetime
from polizas.models import Poliza, Cliente

@login_required
def reportes_dashboard(request):
    user = request.user
    
    # Filtros de fecha
    fecha_inicio_str = request.GET.get('fecha_inicio')
    fecha_fin_str = request.GET.get('fecha_fin')
    
    polizas_query = Poliza.objects.filter(usuario=user)
    
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

    # 2. Reporte de Comisiones
    comisiones = polizas_query.aggregate(
        cobradas=Sum('comision_monto', filter=models.Q(comision_cobrada=True)),
        pendientes=Sum('comision_monto', filter=models.Q(comision_cobrada=False)),
    )
    
    # 3. Reporte de Cartera (Pólizas por Ramo)
    cartera_por_ramo = polizas_query.values('ramo_tipo_seguro').annotate(
        cantidad=Count('id')
    ).order_by('-cantidad')

    context = {
        'produccion_por_mes': produccion_por_mes,
        'comisiones': comisiones,
        'cartera_por_ramo': cartera_por_ramo,
        'fecha_inicio': fecha_inicio_str,
        'fecha_fin': fecha_fin_str
    }
    return render(request, 'reportes/reportes_dashboard.html', context)

@login_required
def exportar_polizas_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="polizas_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Numero Poliza', 'Cliente', 'Aseguradora', 'Ramo', 'Fecha Inicio', 'Fecha Fin', 'Prima Anual'])
    
    polizas = Poliza.objects.filter(usuario=request.user).select_related('cliente', 'aseguradora')
    for poliza in polizas:
        writer.writerow([poliza.numero_poliza, poliza.cliente.nombre_completo, poliza.aseguradora.nombre, poliza.ramo_tipo_seguro, poliza.fecha_inicio_vigencia, poliza.fecha_fin_vigencia, poliza.prima_total_anual])
        
    return response