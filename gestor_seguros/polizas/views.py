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
from .forms import PolizaForm, AseguradoraForm,PagoCuotaForm,SiniestroForm,AseguradoForm 
from clientes.models import Cliente # Para el selector de clientes
from django.db.models import F, ExpressionWrapper, DateField
from django.db.models.functions import ExtractMonth, ExtractDay
from django.forms import inlineformset_factory
import copy,json
from .mixins import OwnerRequiredMixin


# --- Factory para el Formset de Asegurados ---
AseguradoFormSet = inlineformset_factory(
    Poliza,
    Asegurado,
    form=AseguradoForm,
    extra=0, 
    min_num=1,
    validate_min=True,
    can_delete=True,
    fk_name='poliza'
)

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
        if self.request.POST:
            context['asegurados_formset'] = AseguradoFormSet(self.request.POST, prefix='asegurados')
        else:
            context['asegurados_formset'] = AseguradoFormSet(prefix='asegurados')
        context['titulo_pagina'] = "Crear Nueva Póliza"
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        asegurados_formset = context['asegurados_formset']
        
        if asegurados_formset.is_valid():
            with transaction.atomic():
                form.instance.usuario = self.request.user
                self.object = form.save()
                asegurados_formset.instance = self.object
                asegurados_formset.save()
            # La línea de abajo se encarga del mensaje de éxito
            return super().form_valid(form)
        else:
            # Si el formset falla por otra razón (ej. formato de fecha), manejamos el error
            return self.form_invalid(form)

    def form_invalid(self, form):
        asegurados_formset = AseguradoFormSet(self.request.POST, prefix='asegurados')
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        
        # Depuración: Imprime los errores en los logs del servidor
        print("--- Errores del Formulario Principal ---")
        print(form.errors)
        print("--- Errores del Formset de Asegurados ---")
        print(asegurados_formset.errors)
        print(asegurados_formset.non_form_errors())

        return self.render_to_response(
            self.get_context_data(form=form, asegurados_formset=asegurados_formset)
        )
    
    def get_success_url(self):
        return reverse_lazy('polizas:detalle_poliza', kwargs={'pk': self.object.pk})

class PolizaUpdateView(LoginRequiredMixin, OwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Poliza
    form_class = PolizaForm
    template_name = 'polizas/poliza_form.html'
    success_message = "Póliza actualizada exitosamente."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'asegurados_formset' not in kwargs: # Evitar sobreescribir si viene de form_invalid
            if self.request.POST:
                context['asegurados_formset'] = AseguradoFormSet(self.request.POST, instance=self.object, prefix='asegurados')
            else:
                context['asegurados_formset'] = AseguradoFormSet(instance=self.object, prefix='asegurados')
        context['titulo_pagina'] = "Editar Póliza"
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        asegurados_formset = context['asegurados_formset']
        
        if asegurados_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                asegurados_formset.save()
            return super().form_valid(form)
        else:
            # Si el formset no es válido, pasamos al método form_invalid
            return self.form_invalid(form)

    def form_invalid(self, form):
        # --- LÓGICA MEJORADA PARA MANEJAR EL ERROR DE ELIMINACIÓN ---
        
        # Instanciamos el formset de nuevo para analizarlo
        asegurados_formset = AseguradoFormSet(self.request.POST, instance=self.object, prefix='asegurados')

        # Verificamos si el ÚNICO error es el de 'submit at least 1 form'
        # y si TODOS los formularios están marcados para borrar o están vacíos.
        is_only_min_form_error = False
        if asegurados_formset.non_form_errors():
            errors = asegurados_formset.non_form_errors().as_data()
            if len(errors) == 1 and errors[0].code == 'too_few_forms':
                is_only_min_form_error = True

        # Verificamos si el usuario realmente está intentando dejar el formset vacío
        all_forms_to_be_deleted = True
        for f in asegurados_formset:
            # Si un formulario tiene datos y no está marcado para borrar, no estamos borrando todo
            if f.has_changed() and not f.cleaned_data.get('DELETE', False):
                all_forms_to_be_deleted = False
                break
        
        # --- CONDICIÓN CLAVE ---
        # Si el único error es el del mínimo de formularios, Y el usuario está borrando/dejando vacíos
        # todos los formularios, entonces consideramos el formset como "válido" para nuestros propósitos.
        if is_only_min_form_error and all_forms_to_be_deleted:
            print("--- DEBUG: Ignorando error 'too_few_forms' porque el usuario está borrando todos los asegurados. ---")
            with transaction.atomic():
                self.object = form.save()
                # Guardamos el formset aunque 'is_valid' sea False,
                # porque lo que hará es procesar las eliminaciones.
                asegurados_formset.save()
            
            # Forzamos la redirección de éxito
            return redirect(self.get_success_url())

        # Si hay otros errores, los mostramos como antes
        messages.error(self.request, 'Por favor, corrige los errores en el formulario.')
        return self.render_to_response(
            self.get_context_data(form=form, asegurados_formset=asegurados_formset)
        )

    def get_success_url(self):
        return reverse_lazy('polizas:detalle_poliza', kwargs={'pk': self.object.pk})
class PolizaDeleteView(LoginRequiredMixin, DeleteView):
    model = Poliza
    template_name = 'polizas/poliza_confirm_delete.html'
    success_url = reverse_lazy('polizas:lista_polizas')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Póliza No. '{obj.numero_poliza}' eliminada exitosamente.")
        return super(PolizaDeleteView, self).delete(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        return self.model.objects.filter(usuario=self.request.user)

@login_required
def renovar_poliza(request, pk):
    poliza_original = get_object_or_404(Poliza, pk=pk, usuario=request.user)
    
    # --- LÓGICA DE RENOVACIÓN CORREGIDA ---
    # La nueva póliza es una copia de la original
    poliza_nueva = poliza_original
    poliza_nueva.pk = None
    poliza_nueva.id = None
    
    # Sumamos exactamente un año a las fechas de vigencia
    if poliza_original.fecha_inicio_vigencia and poliza_original.fecha_fin_vigencia:
        poliza_nueva.fecha_inicio_vigencia = poliza_original.fecha_inicio_vigencia + relativedelta(years=1)
        poliza_nueva.fecha_fin_vigencia = poliza_original.fecha_fin_vigencia + relativedelta(years=1)

    # Reiniciamos los estados para la nueva póliza
    poliza_nueva.estado_poliza = 'EN_TRAMITE' # Inicia como "En Trámite"
    poliza_nueva.comision_cobrada = False
    poliza_nueva.fecha_cobro_comision = None
    poliza_nueva.fecha_emision = timezone.now().date()
    poliza_nueva.numero_poliza = f"{poliza_original.numero_poliza}-R" # Sugerir un nuevo número

    poliza_nueva.save() # Guardamos la nueva póliza

    # Marcamos la póliza original como RENOVADA
    poliza_original.estado_poliza = 'RENOVADA'
    poliza_original.save()

    # Eliminamos los pagos antiguos de la nueva póliza copiada (si los hubiera)
    poliza_nueva.pagos_cuotas.all().delete()

    messages.info(request, f"Póliza {poliza_original.numero_poliza} marcada como renovada. Revisa los detalles de la nueva póliza de renovación.")
    
    # Redirigimos al formulario de EDICIÓN de la NUEVA póliza para confirmar datos
    return redirect('polizas:editar_poliza', pk=poliza_nueva.pk)

# --- Dashboard y Recordatorios ---
@login_required
def dashboard_view(request):
    """
    Vista principal del dashboard que consolida todas las alertas y métricas clave
    para la gestión de la agencia de seguros.
    """
    hoy = timezone.now().date()

    # ==============================================================================
    # 1. QUERIES BASE: Definimos los conjuntos de datos principales una sola vez.
    # ==============================================================================

    # Todas las pólizas del usuario que requieren algún tipo de atención o seguimiento.
    # Excluimos las que están cerradas definitivamente ('CANCELADA', 'RENOVADA').
    polizas_activas_y_pendientes = Poliza.objects.filter(
        usuario=request.user
    ).exclude(
        estado_poliza__in=['CANCELADA', 'RENOVADA']
    ).select_related('cliente', 'aseguradora')

    # ==============================================================================
    # 2. CÁLCULOS PARA LAS SECCIONES DEL DASHBOARD
    # ==============================================================================

    # --- SECCIÓN A: Pólizas que necesitan gestión (Renovaciones / Trámites) ---

    # A.1: Pólizas nuevas o renovadas que están esperando ser activadas.
    polizas_en_tramite = polizas_activas_y_pendientes.filter(
        estado_poliza='EN_TRAMITE'
    ).order_by('fecha_inicio_vigencia')

    # A.2: Pólizas cuya cobertura ya terminó y no han sido renovadas.
    polizas_vencidas = polizas_activas_y_pendientes.filter(
        fecha_fin_vigencia__lt=hoy,
        estado_poliza__in=['VIGENTE', 'PENDIENTE_PAGO'] 
    ).order_by('fecha_fin_vigencia')

    # A.3: Pólizas cuya cobertura está próxima a vencer (en los próximos 30 días).
    polizas_a_vencer_30 = polizas_activas_y_pendientes.filter(
        fecha_fin_vigencia__range=(hoy, hoy + timedelta(days=30))
    ).order_by('fecha_fin_vigencia')
    
    # A.4: Pólizas por Vencer entre 31 y 60 Días (LÓGICA CORRECTA)
    polizas_a_vencer_60 = polizas_activas_y_pendientes.filter(
        fecha_fin_vigencia__range=(hoy + timedelta(days=31), hoy + timedelta(days=60))
    ).order_by('fecha_fin_vigencia')
    # --- FIN SECCIÓN A ---
    # --- SECCIÓN B: Gestión de Cobros de Cuotas ---

    cobros_pendientes_30_dias = []
    cobros_vencidos = []

    # Iteramos sobre las pólizas activas para encontrar cuotas pendientes.
    # Usamos list() para evaluar el queryset una sola vez.
    for poliza in list(polizas_activas_y_pendientes.exclude(frecuencia_pago__in=['UNICO', 'ANUAL'])):
        prox_cobro = poliza.proxima_fecha_cobro
        if prox_cobro:
            dias = (prox_cobro - hoy).days
            if dias < 0:
                cobros_vencidos.append(poliza)
            elif 0 <= dias <= 30:
                cobros_pendientes_30_dias.append(poliza)

    # Ordenamos las listas resultantes en Python.
    cobros_pendientes_30_dias.sort(key=lambda p: p.proxima_fecha_cobro)
    cobros_vencidos.sort(key=lambda p: p.proxima_fecha_cobro)

    # --- SECCIÓN C: Otras Tareas y Recordatorios ---

    # C.1: Comisiones pendientes de cobro en toda la cartera activa.
    # Buscamos comisiones pendientes en TODAS las pólizas del usuario,
    # sin importar su estado (incluso si están renovadas), porque una comisión
    # de una póliza antigua puede seguir pendiente de cobro.
    comisiones_pendientes = Poliza.objects.filter(
        usuario=request.user,
        comision_cobrada=False,
        comision_monto__gt=0
    ).select_related('cliente').order_by('fecha_fin_vigencia')

    # C.2: Cumpleaños del mes actual.
    cumpleaneros_mes = Cliente.objects.filter(
        usuario=request.user,
        fecha_nacimiento__month=hoy.month
    ).order_by('fecha_nacimiento__day')

    # ==============================================================================
    # 3. KPIs (INDICADORES CLAVE) Y DATOS PARA NOTIFICACIONES JS
    # ==============================================================================

    # Indicadores para las tarjetas superiores
    total_clientes = Cliente.objects.filter(usuario=request.user).count()
    total_polizas_vigentes = polizas_activas_y_pendientes.filter(estado_poliza='VIGENTE').count()

    # Datos para las notificaciones "Toast" de JavaScript
    cumpleaneros_hoy = cumpleaneros_mes.filter(fecha_nacimiento__day=hoy.day)
    cumpleaneros_hoy_json = json.dumps([{'nombre': c.nombre_completo} for c in cumpleaneros_hoy])

    polizas_vencen_semana = polizas_activas_y_pendientes.filter(fecha_fin_vigencia__range=(hoy, hoy + timedelta(days=7)))
    polizas_vencen_semana_json = json.dumps([{'numero': p.numero_poliza} for p in polizas_vencen_semana])

    # ==============================================================================
    # 4. CONSTRUCCIÓN DEL CONTEXTO FINAL PARA LA PLANTILLA
    # ==============================================================================
    context = {
        # Fecha de hoy para comparaciones en la plantilla
        'hoy': hoy,
        
        # Listas para las secciones de alertas
        'polizas_en_tramite': polizas_en_tramite,
        'polizas_vencidas': polizas_vencidas,
        'polizas_a_vencer_30': polizas_a_vencer_30,
        'cobros_vencidos': cobros_vencidos,
        'cobros_pendientes_30_dias': cobros_pendientes_30_dias,
        'comisiones_pendientes': comisiones_pendientes,
        'cumpleaneros_mes': cumpleaneros_mes,
        'polizas_a_vencer_60': polizas_a_vencer_60,
        
        # KPIs para las tarjetas
        'total_clientes': total_clientes,
        'total_polizas_vigentes': total_polizas_vigentes,
        
        # Datos JSON para JavaScript
        'cumpleaneros_hoy_json': cumpleaneros_hoy_json,
        'polizas_vencen_semana_json': polizas_vencen_semana_json,

        # Título de la página
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