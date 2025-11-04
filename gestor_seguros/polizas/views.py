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
from django.http import JsonResponse
from bs4 import BeautifulSoup
from django.core.cache import cache
from decimal import Decimal,InvalidOperation
from .mixins import OwnerRequiredMixin


# Constantes para estados de póliza activos
ESTADOS_POLIZA_ACTIVOS = ['VIGENTE', 'PENDIENTE_PAGO']

# --- Vistas para Aseguradoras ---
class AseguradoraListView(LoginRequiredMixin, ListView):
    model = Aseguradora
    template_name = 'polizas/aseguradora_list.html'
    context_object_name = 'aseguradoras'
    paginate_by = 10

class AseguradoraCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Aseguradora
    form_class = AseguradoraForm
    template_name = 'polizas/aseguradora_form.html'
    success_url = reverse_lazy('polizas:lista_aseguradoras')
    success_message = "Aseguradora '%(nombre)s' creada exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Registrar Nueva Aseguradora"
        context['boton_submit'] = "Crear Aseguradora"
        return context
    
    def form_valid(self, form):
        form.instance.usuario = self.request.user # Asigna el usuario
        return super().form_valid(form)
    
class AseguradoraUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Aseguradora
    form_class = AseguradoraForm
    template_name = 'polizas/aseguradora_form.html'
    success_url = reverse_lazy('polizas:lista_aseguradoras')
    success_message = "Aseguradora '%(nombre)s' actualizada exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Editar Aseguradora"
        context['boton_submit'] = "Actualizar Aseguradora"
        return context

class AseguradoraDeleteView(LoginRequiredMixin, DeleteView): # SuccessMessageMixin da problemas con %()s en DeleteView a veces
    model = Aseguradora
    template_name = 'polizas/aseguradora_confirm_delete.html'
    success_url = reverse_lazy('polizas:lista_aseguradoras')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Aseguradora '{obj.nombre}' eliminada exitosamente.")
        return super(AseguradoraDeleteView, self).delete(request, *args, **kwargs)

# --- Vistas para Pólizas ---
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

class PolizaDetailView(LoginRequiredMixin,OwnerRequiredMixin, DetailView):
    model = Poliza
    template_name = 'polizas/poliza_detail.html'
    context_object_name = 'poliza'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        poliza = self.get_object()

        proxima_cuota = poliza.proxima_fecha_cobro
        # Solo mostramos el formulario si hay una próxima cuota pendiente
        if proxima_cuota:

            initial_data = {
                'fecha_pago': timezone.now().date(),
                'monto_pagado': poliza.valor_cuota if poliza.valor_cuota else poliza.prima_total_anual,
                'fecha_cuota_correspondiente': proxima_cuota
            }
            context['pago_form'] = PagoCuotaForm(initial=initial_data)
            
            pago_form = PagoCuotaForm(initial={
                'monto_pagado': poliza.valor_cuota or poliza.prima_total_anual,
                'fecha_cuota_correspondiente': proxima_cuota
            })
            context['pago_form'] = pago_form
        
        context['pagos_realizados'] = poliza.pagos_cuotas.all()


        # Formulario para registrar un nuevo pago
        pago_form = PagoCuotaForm(initial={
            'monto_pagado': poliza.valor_cuota or poliza.prima_total_anual,
            'fecha_cuota_correspondiente': poliza.proxima_fecha_cobro
        })
        context['pago_form'] = pago_form
        
        # Lista de pagos existentes
        context['pagos_realizados'] = poliza.pagos_cuotas.all()

            # Lista de siniestros asociados
        context['siniestros_asociados'] = self.object.siniestros.all()

        
        # ContentType para uso en formularios genéricos
        obj = self.get_object()
        context['content_type'] = ContentType.objects.get_for_model(obj)
        
        return context

    def post(self, request, *args, **kwargs):
        poliza = self.get_object()
        form = PagoCuotaForm(request.POST)


        if not poliza.proxima_fecha_cobro:
            messages.error(request, 'No se pueden registrar más pagos. Todas las cuotas de esta póliza ya han sido cubiertas.')
            return redirect(poliza.get_absolute_url())

        form = PagoCuotaForm(request.POST)

        if form.is_valid():
            nuevo_pago = form.save(commit=False)
            nuevo_pago.poliza = poliza
            nuevo_pago.save()
            messages.success(request, '¡Pago de cuota registrado exitosamente!')
            return redirect(poliza.get_absolute_url())
        else:
            # Si el formulario no es válido, volvemos a renderizar la página con los errores
            context = self.get_context_data()
            context['pago_form'] = form # Pasamos el formulario con errores
            messages.error(request, 'Hubo un error al registrar el pago. Por favor, revisa los datos.')
            return self.render_to_response(context)

class PolizaCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Poliza
    form_class = PolizaForm
    template_name = 'polizas/poliza_form.html'
    success_message = "Póliza creada exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Crear Nueva Póliza"
        if 'formset' not in kwargs:
            if self.request.POST:
                context['formset'] = inlineformset_factory(Poliza, Asegurado, form=AseguradoForm, extra=0, can_delete=True)(self.request.POST, prefix='asegurados')
            else:
                context['formset'] = inlineformset_factory(Poliza, Asegurado, form=AseguradoForm, extra=1, can_delete=True)(prefix='asegurados')
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        
        # --- LÓGICA PARA EL BOTÓN "AÑADIR OTRO" ---
        if 'add_item' in request.POST:
            # Reconstruimos el formset con un formulario extra
            extra_forms = int(request.POST.get('extra_forms', 1)) + 1
            formset = inlineformset_factory(Poliza, Asegurado, form=AseguradoForm, extra=extra_forms, can_delete=True)(request.POST, prefix='asegurados')
            
            # Guardamos el número de extras para la próxima recarga
            form.data = form.data.copy()
            form.data['extra_forms'] = extra_forms
            
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        # --- LÓGICA DE GUARDADO NORMAL ---
        formset = inlineformset_factory(Poliza, Asegurado, form=AseguradoForm, extra=0, can_delete=True)(request.POST, prefix='asegurados')
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.instance.usuario = request.user
                self.object = form.save()
                formset.instance = self.object
                formset.save()
            messages.success(request, "Póliza creada exitosamente.")
            return redirect(self.get_success_url())
        else:
            messages.error(request, "Por favor, corrige los errores.")
            return self.render_to_response(self.get_context_data(form=form, formset=formset))
    
    def get_success_url(self):
        return reverse_lazy('polizas:detalle_poliza', kwargs={'pk': self.object.pk})

class PolizaUpdateView(LoginRequiredMixin, OwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Poliza
    form_class = PolizaForm
    template_name = 'polizas/poliza_form.html'
    success_message = "Póliza actualizada exitosamente."
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Editar Póliza"
        if 'formset' not in kwargs:
            if self.request.POST:
                context['formset'] = inlineformset_factory(Poliza, Asegurado, form=AseguradoForm, extra=0, can_delete=True)(self.request.POST, instance=self.object, prefix='asegurados')
            else:
                context['formset'] = inlineformset_factory(Poliza, Asegurado, form=AseguradoForm, extra=1, can_delete=True)(instance=self.object, prefix='asegurados')
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if 'add_item' in request.POST:
            extra_forms = int(request.POST.get('extra_forms', 1)) + 1
            formset = inlineformset_factory(Poliza, Asegurado, form=AseguradoForm, extra=extra_forms, can_delete=True)(request.POST, instance=self.object, prefix='asegurados')
            
            form.data = form.data.copy()
            form.data['extra_forms'] = extra_forms
            
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        formset = inlineformset_factory(Poliza, Asegurado, form=AseguradoForm, extra=0, can_delete=True)(request.POST, instance=self.object, prefix='asegurados')
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                formset.save()
            messages.success(request, "Póliza actualizada exitosamente.")
            return redirect(self.get_success_url())
        else:
            messages.error(request, "Por favor, corrige los errores.")
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
    
    # --- LÓGICA DE RENOVACIÓN CORREGIDA ---
    # ¡CRUCIAL! Crear una COPIA REAL del objeto de la póliza
    poliza_nueva = copy.copy(poliza_original)
    poliza_nueva.pk = None
    poliza_nueva.id = None
    poliza_nueva.usuario = request.user # Aseguramos que el usuario es el mismo
    
    # Sumamos exactamente un año a las fechas de vigencia
    if poliza_original.fecha_inicio_vigencia and poliza_original.fecha_fin_vigencia:
        poliza_nueva.fecha_inicio_vigencia = poliza_original.fecha_inicio_vigencia + relativedelta(years=1)
        poliza_nueva.fecha_fin_vigencia = poliza_original.fecha_fin_vigencia + relativedelta(years=1)
    else:
        # Si no hay fechas de vigencia, podemos establecer unas por defecto
        poliza_nueva.fecha_inicio_vigencia = timezone.localtime(timezone.now()).date()
        poliza_nueva.fecha_fin_vigencia = timezone.localtime(timezone.now()).date() + relativedelta(years=1)


    # Reiniciamos los estados para la nueva póliza
    poliza_nueva.estado_poliza = 'EN_TRAMITE' # Inicia como "En Trámite"
    poliza_nueva.comision_cobrada = False
    poliza_nueva.fecha_cobro_comision = None
    poliza_nueva.fecha_emision = timezone.localtime(timezone.now()).date()
    # Generar un número de póliza sugerido para la renovación
    # Nos aseguramos de que sea único añadiendo un timestamp si ya existe
    base_numero_poliza = f"{poliza_original.numero_poliza}-R"
    num_suffix = 1
    while Poliza.objects.filter(usuario=request.user, numero_poliza=base_numero_poliza).exists():
        base_numero_poliza = f"{poliza_original.numero_poliza}-R{num_suffix}"
        num_suffix += 1
    poliza_nueva.numero_poliza = base_numero_poliza


    poliza_nueva.save() # Guardamos la nueva póliza


    # --- Copiar Asegurados (y Pagos, Siniestros si fuera necesario) ---
    # Copiamos los asegurados de la póliza original a la nueva.
    for asegurado_original in poliza_original.asegurados.all():
        asegurado_nuevo = copy.copy(asegurado_original)
        asegurado_nuevo.pk = None
        asegurado_nuevo.id = None
        asegurado_nuevo.poliza = poliza_nueva # Asignar a la nueva póliza
        asegurado_nuevo.save()
    
    # IMPORTANTE: Los pagos y siniestros NO deben copiarse en una renovación.
    # Son eventos específicos de la vigencia de la póliza original.


    # Marcamos la póliza original como RENOVADA
    poliza_original.estado_poliza = 'RENOVADA'
    poliza_original.save()

    messages.info(request, f"Póliza {poliza_original.numero_poliza} marcada como renovada. "
                        f"Gestiona los detalles de la nueva póliza de renovación: {poliza_nueva.numero_poliza}.")
    
    # Redirigimos al formulario de EDICIÓN de la NUEVA póliza para confirmar datos
    return redirect('polizas:editar_poliza', pk=poliza_nueva.pk)

# --- Dashboard y Recordatorios ---
@login_required
def dashboard_view(request):
    # Usamos timezone.localtime para asegurarnos de que la fecha 'hoy'
    # corresponde a la zona horaria del servidor (America/Caracas).
    hoy = timezone.localtime(timezone.now()).date()
    
    # --- QUERIES BASE OPTIMIZADOS ---
    
    # Usamos prefetch_related para cargar todos los pagos de cuotas en una sola consulta extra
    prefetch_pagos = Prefetch('pagos_cuotas', queryset=PagoCuota.objects.order_by('-fecha_cuota_correspondiente'))
    
    polizas_activas_y_pendientes = Poliza.objects.filter(
        usuario=request.user
    ).exclude(
        estado_poliza__in=['CANCELADA', 'RENOVADA']
    ).select_related(
        'cliente', 'aseguradora'
    ).prefetch_related(
        prefetch_pagos # <-- APLICAMOS LA PRE-CARGA
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
    
    # Ya no es necesario usar list() aquí, podemos iterar directamente sobre el queryset
    for poliza in polizas_activas_y_pendientes.exclude(frecuencia_pago__in=['UNICO', 'ANUAL']):
        # Esta llamada ahora es casi instantánea, porque los pagos ya están en memoria.
        # No se realiza una nueva consulta a la BD.
        prox_cobro = poliza.proxima_fecha_cobro
        if prox_cobro:
            dias = (prox_cobro - hoy).days
            if dias < 0:
                cobros_vencidos.append(poliza)
            elif 0 <= dias <= 30:
                cobros_pendientes_30_dias.append(poliza)

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
def registrar_pago_rapido(request, pk):
    # Solo permitimos peticiones POST para esta acción por seguridad
    if request.method == 'POST':
        poliza = get_object_or_404(Poliza, pk=pk, usuario=request.user)
        
        # Obtenemos la fecha de la cuota desde los datos del formulario que enviaremos
        fecha_cuota_str = request.POST.get('fecha_cuota')
        
        if fecha_cuota_str:
            fecha_cuota = parse_date(fecha_cuota_str)
            
            # Verificamos que no estemos registrando un pago duplicado para esa cuota
            if not PagoCuota.objects.filter(poliza=poliza, fecha_cuota_correspondiente=fecha_cuota).exists():
                PagoCuota.objects.create(
                    poliza=poliza,
                    fecha_pago=timezone.now().date(),
                    monto_pagado=poliza.valor_cuota or poliza.prima_total_anual,
                    fecha_cuota_correspondiente=fecha_cuota,
                    notas="Pago rápido registrado desde el dashboard."
                )
                messages.success(request, f"Pago para la póliza {poliza.numero_poliza} registrado exitosamente.")
            else:
                messages.warning(request, f"El pago para esa cuota de la póliza {poliza.numero_poliza} ya había sido registrado.")
        else:
            messages.error(request, "No se proporcionó la fecha de la cuota para registrar el pago.")
            
    # Redirigimos siempre al dashboard
    return redirect('dashboard')

#---(VISTAS SINIESTROS)---
class SiniestroCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Siniestro
    form_class = SiniestroForm
    template_name = 'polizas/siniestro_form.html'
    success_message = "Siniestro reportado exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['poliza'] = get_object_or_404(Poliza, pk=self.kwargs['poliza_pk'], usuario=self.request.user)
        context['titulo_pagina'] = "Reportar Nuevo Siniestro"
        return context

    def form_valid(self, form):
        poliza = get_object_or_404(Poliza, pk=self.kwargs['poliza_pk'], usuario=self.request.user)
        form.instance.poliza = poliza
        form.instance.usuario = self.request.user
        return super().form_valid(form)

class SiniestroDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = Siniestro
    template_name = 'polizas/siniestro_detail.html'
    
    def get_queryset(self):
        return super().get_queryset().select_related('poliza', 'poliza__cliente')

class SiniestroUpdateView(LoginRequiredMixin, OwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Siniestro
    form_class = SiniestroForm
    template_name = 'polizas/siniestro_form.html'
    success_message = "Siniestro actualizado exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo_pagina'] = "Editar Siniestro"
        return context

class SiniestroDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Siniestro
    template_name = 'polizas/siniestro_confirm_delete.html'
    
    def get_success_url(self):
        messages.success(self.request, "Siniestro eliminado exitosamente.")
        # Redirige al detalle de la póliza a la que pertenecía el siniestro
        return reverse_lazy('polizas:detalle_poliza', kwargs={'pk': self.object.poliza.pk})
#---(END VISTAS SINIESTROS)---

#<--------- ELIMINAR PAGO CUOTA POR ERROR --------->
@login_required
def eliminar_pago_cuota(request, pk):
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

#<--------- END ELIMINAR PAGO CUOTA POR ERROR --------->

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