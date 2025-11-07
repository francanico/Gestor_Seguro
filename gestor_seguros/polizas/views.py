# polizas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from .models import Poliza, Aseguradora,PagoCuota,Siniestro,Asegurado 
from .forms import PolizaForm, AseguradoraForm,PagoCuotaForm,SiniestroForm,AseguradoForm,AseguradoFormSet 
from clientes.models import Cliente # Para el selector de clientes
from django.db.models import F,Prefetch
from django.forms import inlineformset_factory
import copy,json,requests
from django.http import JsonResponse, HttpResponseRedirect
from bs4 import BeautifulSoup
from django.core.cache import cache
from decimal import Decimal,InvalidOperation
from .mixins import OwnerRequiredMixin


# Constantes para estados de póliza activos
ESTADOS_POLIZA_ACTIVOS = ['VIGENTE', 'PENDIENTE_PAGO']

# ==========================================================
# VISTAS PARA EL CRUD DE ASEGURADORAS (CÓDIGO FINAL)
# ==========================================================

class AseguradoraListView(LoginRequiredMixin, ListView):
    model = Aseguradora
    template_name = 'polizas/aseguradora_list.html'
    context_object_name = 'aseguradoras'
    paginate_by = 15

    def get_queryset(self):
        return Aseguradora.objects.filter(usuario=self.request.user).order_by('nombre')

class AseguradoraDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = Aseguradora
    template_name = 'polizas/aseguradora_detail.html'
    context_object_name = 'aseguradora'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context['polizas_asociadas'] = obj.polizas.filter(usuario=self.request.user).select_related('cliente').order_by('-fecha_fin_vigencia')
        context['content_type'] = ContentType.objects.get_for_model(obj)
        return context

class AseguradoraCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Aseguradora
    form_class = AseguradoraForm
    template_name = 'polizas/aseguradora_form.html'
    success_url = reverse_lazy('polizas:lista_aseguradoras')
    success_message = "Aseguradora '%(nombre)s' creada exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Registrar Nueva Aseguradora"
        return context

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)

class AseguradoraUpdateView(LoginRequiredMixin, OwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Aseguradora
    form_class = AseguradoraForm
    template_name = 'polizas/aseguradora_form.html'
    success_url = reverse_lazy('polizas:lista_aseguradoras')
    success_message = "Aseguradora '%(nombre)s' actualizada exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Editar Aseguradora"
        return context

class AseguradoraDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Aseguradora
    template_name = 'polizas/aseguradora_confirm_delete.html'
    success_url = reverse_lazy('polizas:lista_aseguradoras')
    context_object_name = 'aseguradora'
    
    def form_valid(self, form):
        messages.success(self.request, f"Aseguradora '{self.object.nombre}' eliminada exitosamente.")
        return super().form_valid(form)


# ==========================================================
# VISTAS PARA EL CRUD DE PÓLIZAS
# ==========================================================

class PolizaListView(LoginRequiredMixin, ListView):
    model = Poliza
    template_name = 'polizas/poliza_list.html'
    context_object_name = 'polizas'
    paginate_by = 10

    def get_queryset(self):
        queryset = Poliza.objects.select_related('cliente', 'aseguradora')
        filtro = self.request.GET.get('filtro_dashboard')
        hoy = timezone.now().date()
        ESTADOS_RELEVANTES = ['VIGENTE', 'PENDIENTE_PAGO']

        if filtro == 'vencidas':
            queryset = queryset.filter(fecha_fin_vigencia__lt=hoy, estado_poliza__in=ESTADOS_RELEVANTES)
            self.request.session['titulo_lista_polizas'] = "Pólizas Vencidas" # Opcional para el título
        elif filtro == 'vencer30':
            proximos_30_dias = hoy + timedelta(days=30)
            queryset = queryset.filter(fecha_fin_vigencia__gte=hoy, fecha_fin_vigencia__lte=proximos_30_dias, estado_poliza__in=ESTADOS_RELEVANTES)
            self.request.session['titulo_lista_polizas'] = "Pólizas Venciendo en Menos de 30 Días"
        elif filtro == 'vencer60':
            proximos_30_dias = hoy + timedelta(days=30)
            proximos_60_dias = hoy + timedelta(days=60)
            queryset = queryset.filter(fecha_fin_vigencia__gt=proximos_30_dias, fecha_fin_vigencia__lte=proximos_60_dias, estado_poliza__in=ESTADOS_RELEVANTES)
            self.request.session['titulo_lista_polizas'] = "Pólizas Venciendo en 31-60 Días"
        else:
            # Podrías limpiar el título si no hay filtro o es otro tipo de filtro
            if 'titulo_lista_polizas' in self.request.session:
                del self.request.session['titulo_lista_polizas']


        # También podrías añadir otros filtros aquí, por ejemplo, búsqueda por texto
        # query_busqueda = self.request.GET.get('q')
        # if query_busqueda:
        #     queryset = queryset.filter(numero_poliza__icontains=query_busqueda) # O buscar en más campos

        return queryset.order_by('-fecha_fin_vigencia')


    def get_queryset(self):
        # Filtra el queryset para mostrar solo los clientes del usuario actual
        queryset = super().get_queryset().filter(usuario=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasar el título dinámico a la plantilla si se estableció
        context['titulo_dinamico_lista'] = self.request.session.get('titulo_lista_polizas', "Lista de Pólizas")
        # Limpiar el título de la sesión después de usarlo para que no persista
        # if 'titulo_lista_polizas' in self.request.session:
        #     del self.request.session['titulo_lista_polizas']
        return context

class PolizaDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = Poliza
    template_name = 'polizas/poliza_detail.html'
    context_object_name = 'poliza'

    def get_queryset(self):
        """
        Optimiza la carga de datos relacionados para evitar múltiples consultas a la BD.
        """
        return super().get_queryset().select_related(
            'cliente', 'aseguradora'
        ).prefetch_related(
            'asegurados', 'cuotas', 'siniestros', 'documentos'
        )

    def get_context_data(self, **kwargs):
        """
        Prepara todo el contexto necesario para la plantilla de detalle.
        """
        context = super().get_context_data(**kwargs)
        poliza = self.get_object()
            # maneja la lista de cuotas directamente.
        
        # Pasamos el ContentType para la sección de documentos.
        context['content_type'] = ContentType.objects.get_for_model(poliza)
        
        return context

    def post(self, request, *args, **kwargs):
        """
        Maneja la acción de "Marcar como Pagada" para una cuota específica.
        """
        poliza = self.get_object()
        
        # El formulario en la plantilla envía el 'pk' de la cuota que se quiere pagar.
        cuota_pk_a_pagar = request.POST.get('cuota_pk')
        
        if cuota_pk_a_pagar:
            try:
                # Buscamos la cuota, asegurándonos que pertenece a esta póliza y a este usuario
                cuota = PagoCuota.objects.get(pk=cuota_pk_a_pagar, poliza=poliza, poliza__usuario=request.user)
                
                if cuota.estado == 'PENDIENTE':
                    cuota.estado = 'PAGADO'
                    cuota.fecha_de_pago_realizado = timezone.now().date()
                    cuota.save()
                    messages.success(request, f"La cuota con vencimiento el {cuota.fecha_vencimiento_cuota.strftime('%d/%m/%Y')} ha sido marcada como pagada.")
                else:
                    messages.warning(request, "Esta cuota ya había sido marcada como pagada.")
                    
            except PagoCuota.DoesNotExist:
                messages.error(request, "La cuota que intentas pagar no es válida.")
        
        # Redirigimos siempre de vuelta a la página de detalle de la póliza.
        return redirect(poliza.get_absolute_url())

class PolizaUpdateView(LoginRequiredMixin, OwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Poliza
    form_class = PolizaForm
    template_name = 'polizas/poliza_form.html'
    success_message = "Póliza actualizada exitosamente."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Editar Póliza"
        # Usamos 'formset' consistentemente
        if 'formset' not in kwargs:
            if self.request.POST:
                context['formset'] = AseguradoFormSet(self.request.POST, instance=self.object, prefix='asegurados')
            else:
                context['formset'] = AseguradoFormSet(instance=self.object, prefix='asegurados')
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = AseguradoFormSet(request.POST, instance=self.object, prefix='asegurados') # <-- Definimos 'formset'

        if 'add_item' in request.POST:
            # La lógica de recarga de página para añadir un ítem.
            # Necesitamos reconstruir el formset con un extra.
            # OJO: Esta es la lógica para el método SIN JS.
            form_data = request.POST.copy()
            form_count = int(form_data.get('asegurados-TOTAL_FORMS', 0))
            form_data['asegurados-TOTAL_FORMS'] = str(form_count + 1)
            
            # Recreamos el formset con los datos modificados
            formset_con_extra = AseguradoFormSet(form_data, instance=self.object, prefix='asegurados')
            return self.render_to_response(self.get_context_data(form=form, formset=formset_con_extra))

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)
            
    def form_valid(self, form, formset):
        with transaction.atomic():
            self.object = form.save()
            formset.save()
        return super().form_valid(form)
    
    def form_invalid(self, form, formset):
        messages.error(self.request, "Por favor, corrige los errores.")
        return self.render_to_response(self.get_context_data(form=form, formset=formset))
    
    def get_success_url(self):
        return reverse_lazy('polizas:detalle_poliza', kwargs={'pk': self.object.pk})

class PolizaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Poliza
    form_class = PolizaForm
    template_name = 'polizas/poliza_form.html'
    success_message = "Póliza creada exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Crear Nueva Póliza"
        # Usamos 'formset' consistentemente
        if 'formset' not in kwargs:
            if self.request.POST:
                context['formset'] = AseguradoFormSet(self.request.POST, prefix='asegurados')
            else:
                context['formset'] = AseguradoFormSet(prefix='asegurados')
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        formset = AseguradoFormSet(request.POST, prefix='asegurados') # <-- Definimos 'formset'

        if 'add_item' in request.POST:
            # Esta lógica ahora es innecesaria con el nuevo enfoque, la simplificamos
            # pero la dejamos por si decides volver a ella.
            # Lo importante es que no causa el error.
            pass

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def form_valid(self, form, formset):
        with transaction.atomic():
            form.instance.usuario = self.request.user
            self.object = form.save()
            formset.instance = self.object
            formset.save()
        return super().form_valid(form)

    def form_invalid(self, form, formset):
        messages.error(self.request, "Por favor, corrige los errores.")
        return self.render_to_response(self.get_context_data(form=form, formset=formset))
    
    def get_success_url(self):
        return reverse_lazy('polizas:detalle_poliza', kwargs={'pk': self.object.pk})

class PolizaDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Poliza
    template_name = 'polizas/poliza_confirm_delete.html'
    success_url = reverse_lazy('polizas:lista_polizas')
    context_object_name = 'poliza' # Es buena práctica definirlo

    def form_valid(self, form):
        # Sobreescribimos form_valid para añadir un mensaje de éxito
        messages.success(self.request, f"La póliza '{self.object.numero_poliza}' ha sido eliminada exitosamente.")
        return super().form_valid(form)
    
    # Nos aseguramos de que el mixin de propietario se aplique correctamente
    def get_queryset(self):
        return super().get_queryset()

# --- VISTA PARA RENOVAR PÓLIZA ---
@login_required
def renovar_poliza(request, pk):
    poliza_original = get_object_or_404(Poliza, pk=pk, usuario=request.user)

    # 1. Marcamos la póliza original como RENOVADA y la guardamos primero.
    poliza_original.estado_poliza = 'RENOVADA'
    poliza_original.save()

    # --- LÓGICA DE RENOVACIÓN CORREGIDA ---
    
    # 2. Calculamos los nuevos valores.
    nuevo_ano_vigencia = poliza_original.fecha_fin_vigencia.year
    nuevo_numero_poliza = f"{poliza_original.numero_poliza}-{nuevo_ano_vigencia}"

    # 3. Creamos la nueva instancia de póliza pasando todos los argumentos.
    poliza_nueva = Poliza(
        usuario=poliza_original.usuario,
        cliente=poliza_original.cliente,
        aseguradora=poliza_original.aseguradora,
        ramo_tipo_seguro=poliza_original.ramo_tipo_seguro,
        descripcion_bien_asegurado=poliza_original.descripcion_bien_asegurado,
        prima_total_anual=poliza_original.prima_total_anual,
        frecuencia_pago=poliza_original.frecuencia_pago,
        valor_cuota=poliza_original.valor_cuota,
        comision_monto=poliza_original.comision_monto,
        
        # Valores específicos de la renovación
        numero_poliza=nuevo_numero_poliza, # <-- Usamos la variable correcta
        renovacion_de=poliza_original,
        fecha_inicio_vigencia=poliza_original.fecha_fin_vigencia,
        fecha_fin_vigencia=poliza_original.fecha_fin_vigencia + relativedelta(years=1),
        fecha_emision=timezone.now().date(),
        estado_poliza='EN_TRAMITE',
        comision_cobrada=False,
    )
    
    # 4. Guardamos la nueva póliza.
    poliza_nueva.save()

    # 5. Copiamos los asegurados de la póliza original a la nueva.
    for asegurado in poliza_original.asegurados.all():
        asegurado.pk = None # Anula el ID para crear una nueva instancia
        asegurado.id = None
        asegurado.poliza = poliza_nueva
        asegurado.save()

    # 6. Generamos el nuevo plan de pagos para la póliza renovada.
    poliza_nueva.generar_plan_de_pagos()

    messages.success(request, f"Póliza '{poliza_original.numero_poliza}' renovada como '{poliza_nueva.numero_poliza}'.")
    
    # Redirigimos al formulario de EDICIÓN de la nueva póliza.
    return redirect('polizas:editar_poliza', pk=poliza_nueva.pk)

@login_required
def cancelar_renovacion(request, pk):
    """
    Busca la renovación de una póliza, la elimina, y revierte la
    póliza original a su estado anterior.
    """
    poliza_original = get_object_or_404(Poliza, pk=pk, usuario=request.user)

    # Buscamos la póliza que fue creada como renovación de esta
    poliza_renovada = Poliza.objects.filter(renovacion_de=poliza_original, usuario=request.user).first()

    if request.method == 'POST':
        if poliza_renovada:
            # Eliminamos la póliza de renovación que se creó por error
            poliza_renovada.delete()
            
            # Revertimos el estado de la póliza original a 'VIGENTE'
            poliza_original.estado_poliza = 'VIGENTE'
            poliza_original.save()
            
            messages.success(request, f"La renovación de la póliza '{poliza_original.numero_poliza}' ha sido cancelada.")
        else:
            messages.warning(request, "No se encontró una póliza de renovación para cancelar, pero se ha revertido el estado de la póliza original.")
            # Aunque no haya renovación que borrar, igual revertimos el estado
            poliza_original.estado_poliza = 'VIGENTE'
            poliza_original.save()
            
        return redirect(poliza_original.get_absolute_url())

    return render(request, 'polizas/cancelar_renovacion_confirm.html', {
        'poliza_original': poliza_original,
        'poliza_renovada': poliza_renovada
    })
# --- Dashboard y Recordatorios ---
@login_required
def dashboard_view(request):
    # Usamos timezone.localtime para asegurarnos de que la fecha 'hoy'
    # corresponde a la zona horaria del servidor (America/Caracas).
    hoy = timezone.localtime(timezone.now()).date()
    
    # --- QUERIES BASE OPTIMIZADOS ---
    
    # Usamos prefetch_related para cargar todos los pagos de cuotas en una sola consulta extra
    prefetch_pagos = Prefetch('cuotas', queryset=PagoCuota.objects.order_by('fecha_vencimiento_cuota'))
    
    polizas_activas_y_pendientes = Poliza.objects.filter(
        usuario=request.user
    ).exclude(
        estado_poliza__in=['CANCELADA', 'RENOVADA']
    ).select_related(
        'cliente', 'aseguradora'
    ).prefetch_related(
        prefetch_pagos
    )
    # --- CÁLCULOS PARA EL DASHBOARD ---

    # A. Gestión de Renovaciones
    polizas_en_tramite = polizas_activas_y_pendientes.filter(estado_poliza='EN_TRAMITE').order_by('fecha_inicio_vigencia')
    polizas_vencidas = polizas_activas_y_pendientes.filter(fecha_fin_vigencia__lt=hoy, estado_poliza__in=['VIGENTE', 'PENDIENTE_PAGO']).order_by('fecha_fin_vigencia')
    polizas_a_vencer_30 = polizas_activas_y_pendientes.filter(fecha_fin_vigencia__range=(hoy, hoy + timedelta(days=30))).order_by('fecha_fin_vigencia')

    # B. Gestión de Cobros de Cuotas
    # --- LÓGICA PARA PRÓXIMOS COBROS (AHORA MUCHO MÁS RÁPIDA) ---
    cobros_pendientes_30_dias = []
    cobros_vencidos = []

# --- LÓGICA PARA COBROS ---
    cuotas_pendientes = PagoCuota.objects.filter(
        poliza__usuario=request.user,
        estado='PENDIENTE'
    ).select_related('poliza', 'poliza__cliente')
    
    cobros_vencidos = cuotas_pendientes.filter(fecha_vencimiento_cuota__lt=hoy).order_by('fecha_vencimiento_cuota')
    cobros_pendientes_30_dias = cuotas_pendientes.filter(fecha_vencimiento_cuota__range=(hoy, hoy + timedelta(days=30))).order_by('fecha_vencimiento_cuota')

    # C. Comisiones
    comisiones_pendientes = Poliza.objects.filter(usuario=request.user, comision_cobrada=False, comision_monto__gt=0).select_related('cliente').order_by('fecha_fin_vigencia')

    # D. CUMPLEAÑOS (LÓGICA SIMPLE Y CONSCIENTE DE TIMEZONE)
    # =========================================================
    
    # Obtenemos la fecha local correcta para evitar discrepancias UTC
    fecha_local_hoy = timezone.localtime(timezone.now()).date()
    mes_actual = fecha_local_hoy.month
    
    # La consulta ahora usa solo el modelo Cliente, que es más simple y robusto
    cumpleaneros_mes = Cliente.objects.filter(
        usuario=request.user,
        fecha_nacimiento__isnull=False,
        fecha_nacimiento__month=mes_actual
    ).order_by('fecha_nacimiento__day')


    # --- KPIs Y DATOS JS ---
    total_clientes = Cliente.objects.filter(usuario=request.user).count()
    total_polizas_vigentes = polizas_activas_y_pendientes.filter(estado_poliza='VIGENTE').count()
    
    # --- LÓGICA CORREGIDA PARA NOTIFICACIONES JS ---
    # Filtramos el queryset 'cumpleaneros_mes' que ya tenemos
    cumpleaneros_hoy = cumpleaneros_mes.filter(fecha_nacimiento__day=fecha_local_hoy.day)
    # Convertimos el queryset de objetos Cliente a JSON
    cumpleaneros_hoy_json = json.dumps([{'nombre': c.nombre_completo} for c in cumpleaneros_hoy])
    # Pólizas que vencen en la próxima semana    
    polizas_vencen_semana = polizas_activas_y_pendientes.filter(fecha_fin_vigencia__range=(hoy, hoy + timedelta(days=7)))
    polizas_vencen_semana_json = json.dumps([{'numero': p.numero_poliza} for p in polizas_vencen_semana])

    # --- CONTEXTO FINAL ---
    context = {
        'hoy': hoy,
        'polizas_en_tramite': polizas_en_tramite,
        'polizas_vencidas': polizas_vencidas,
        'polizas_a_vencer_30': polizas_a_vencer_30,
        'cobros_vencidos': cobros_vencidos,
        'cobros_pendientes_30_dias': cobros_pendientes_30_dias,
        'comisiones_pendientes': comisiones_pendientes,
        'cumpleaneros_mes': cumpleaneros_mes, 
        'total_clientes': total_clientes,
        'total_polizas_vigentes': total_polizas_vigentes,
        'cumpleaneros_hoy_json': cumpleaneros_hoy_json,
        'polizas_vencen_semana_json': polizas_vencen_semana_json,
        'titulo_pagina': "Dashboard de Pólizas",
    }
    
    return render(request, 'polizas/dashboard.html', context)

# ---  VISTA DE ACCIÓN RÁPIDA PARA REGISTRAR PAGO ---
@login_required
def registrar_pago_rapido(request, pk_cuota): # 'pk' ahora es de la cuota
    if request.method == 'POST':
        cuota = get_object_or_404(PagoCuota, pk=pk_cuota, poliza__usuario=request.user)
        cuota.estado = 'PAGADO'
        cuota.fecha_de_pago_realizado = timezone.now().date()
        cuota.save()
        messages.success(request, "Cuota marcada como pagada.")
    return redirect('dashboard')

@login_required
def marcar_cuota_pagada(request, pk_cuota):
    cuota = get_object_or_404(PagoCuota, pk=pk_cuota, poliza__usuario=request.user)
    if request.method == 'POST':
        cuota.estado = 'PAGADO'
        cuota.fecha_de_pago_realizado = timezone.now().date()
        cuota.save()
        
        # --- LÍNEA CORREGIDA ---
        # Usamos el método .strftime() para formatear la fecha
        fecha_formateada = cuota.fecha_vencimiento_cuota.strftime('%d/%m/%Y')
        messages.success(request, f"Cuota del {fecha_formateada} marcada como pagada.")
        
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

#---(VISTAS SINIESTROS)---
class SiniestroCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Siniestro
    form_class = SiniestroForm
    template_name = 'polizas/siniestro_form.html'
    success_message = "Siniestro reportado exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Asegura que solo se puedan crear siniestros para pólizas del usuario
        context['poliza'] = get_object_or_404(Poliza, pk=self.kwargs['poliza_pk'], usuario=self.request.user)
        context['titulo_pagina'] = "Reportar Nuevo Siniestro"
        return context

    def form_valid(self, form):
        poliza = get_object_or_404(Poliza, pk=self.kwargs['poliza_pk'], usuario=self.request.user)
        form.instance.poliza = poliza
        form.instance.usuario = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        # Redirige al detalle del siniestro recién creado
        return reverse_lazy('polizas:detalle_siniestro', kwargs={'pk': self.object.pk})

class SiniestroDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = Siniestro
    template_name = 'polizas/siniestro_detail.html'
    context_object_name = 'siniestro' # Es buena práctica definir el nombre del objeto
    
    def get_queryset(self):
        return super().get_queryset().select_related('poliza', 'poliza__cliente')

    # --- MÉTODO AÑADIDO ---
    def get_context_data(self, **kwargs):
        """
        Añade el 'content_type' al contexto para la sección de documentos.
        """
        context = super().get_context_data(**kwargs)
        
        # Obtenemos el objeto actual (el siniestro)
        obj = self.get_object()
        
        # Pasamos su ContentType a la plantilla
        context['content_type'] = ContentType.objects.get_for_model(obj)
        
        return context

class SiniestroUpdateView(LoginRequiredMixin, OwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Siniestro
    form_class = SiniestroForm
    template_name = 'polizas/siniestro_form.html'
    success_message = "Siniestro actualizado exitosamente."
    context_object_name = 'siniestro' # Buena práctica

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Editar Siniestro"
        return context

class SiniestroDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Siniestro
    template_name = 'polizas/siniestro_confirm_delete.html'
    context_object_name = 'siniestro' # Buena práctica
    
    def get_success_url(self):
        messages.success(self.request, "Siniestro eliminado exitosamente.")
        return reverse_lazy('polizas:detalle_poliza', kwargs={'pk': self.object.poliza.pk})
#---(END VISTAS SINIESTROS)---

#<--------- CANCELAR PAGO CUOTA POR ERROR --------->
@login_required
def cancelar_pago_cuota(request, pk_cuota):
    """
    Revierte una cuota del estado 'PAGADO' al estado 'PENDIENTE'.
    """
    # Buscamos la cuota, asegurándonos de que pertenece al usuario.
    cuota = get_object_or_404(PagoCuota, pk=pk_cuota, poliza__usuario=request.user)

    if request.method == 'POST':
        if cuota.estado == 'PAGADO':
            cuota.estado = 'PENDIENTE'
            cuota.fecha_de_pago_realizado = None # Limpiamos la fecha del pago
            cuota.notas_pago = f"Pago revertido por el usuario el {timezone.now().strftime('%d/%m/%Y')}. {cuota.notas_pago or ''}" # Opcional: añade una nota
            cuota.save()
            messages.success(request, "El pago ha sido revertido a pendiente exitosamente.")
        else:
            messages.warning(request, "Esta cuota no estaba marcada como pagada.")
    
    # Redirigimos de vuelta a la página de detalle de la póliza.
    return redirect(cuota.poliza.get_absolute_url())
    try:
        # Intentamos obtener el objeto que cumpla ambas condiciones
        pago = PagoCuota.objects.get(pk=pk, poliza__usuario=request.user)
    except PagoCuota.DoesNotExist:
        # Si el objeto no existe o no pertenece al usuario, 'get' falla
        # y entramos en este bloque de excepción.
        messages.warning(request, "El pago que intentas eliminar no existe o ya fue eliminado.")
        # Redirigimos al usuario al dashboard para evitar el error 404
        return redirect('dashboard') 

    # Si el objeto sí se encontró, guardamos la URL de la póliza para la redirección
    poliza_url = pago.poliza.get_absolute_url()

    if request.method == 'POST':
        pago.delete()
        messages.success(request, "El pago ha sido eliminado exitosamente.")
        return redirect(poliza_url)
    
    # Si es una petición GET, mostramos la página de confirmación normal
    return render(request, 'polizas/pago_cuota_confirm_delete.html', {'pago': pago})

#<--------- END CANCELAR PAGO CUOTA POR ERROR --------->
@login_required
def obtener_tasa_bcv_api(request):
    CACHE_KEY = 'tasa_bcv_usd'
    tasa_str = cache.get(CACHE_KEY)
    
    if not tasa_str:
        try:
            url = 'https://www.bcv.org.ve/' # <-- CAMBIO: A veces la raíz es más estable
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
            
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # --- LÓGICA DE SCRAPING MEJORADA Y MÁS SEGURA ---
            usd_div = soup.find('div', id='dolar')
            if not usd_div:
                raise ValueError("No se pudo encontrar el div con id='dolar'. La estructura de la página del BCV puede haber cambiado.")
                
            strong_tag = usd_div.find('strong')
            if not strong_tag:
                raise ValueError("No se pudo encontrar la etiqueta <strong> dentro del div 'dolar'.")

            tasa_raw_str = strong_tag.get_text(strip=True)
            if not tasa_raw_str:
                raise ValueError("La etiqueta <strong> para la tasa del dólar está vacía.")

            # Limpiamos el string: quitamos puntos de miles y cambiamos coma decimal a punto
            tasa_limpia_str = tasa_raw_str.replace('.', '').replace(',', '.')
            tasa_decimal = Decimal(tasa_limpia_str)
            
            tasa_str = str(tasa_decimal)
            cache.set(CACHE_KEY, tasa_str, timeout=43200) # 12 horas
            
            print(f"TASA BCV OBTENIDA (SCRAPING): {tasa_str}")

        except (requests.RequestException, ValueError, InvalidOperation, AttributeError) as e:
            # Si el scraping falla, devolvemos un error claro
            error_message = f'Error al hacer scraping en BCV: {str(e)}'
            print(error_message)
            return JsonResponse({'error': error_message}, status=503) # 503: Service Unavailable
    else:
        print(f"TASA BCV OBTENIDA (CACHE): {tasa_str}")

    return JsonResponse({'tasa_usd': tasa_str})