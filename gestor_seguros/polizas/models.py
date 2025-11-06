# polizas/models.py
from django.db import models
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from django.conf import settings 
from clientes.models import Cliente 
from dateutil.relativedelta import relativedelta 
from django.contrib.contenttypes.fields import GenericRelation
from documentos.models import Documento

class Aseguradora(models.Model):

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='aseguradoras')
    nombre = models.CharField(max_length=150, unique=True, verbose_name="Nombre de la Aseguradora")
    rif = models.CharField(max_length=20, blank=True, null=True, verbose_name="RIF")
    contacto_nombre = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre de Contacto")
    contacto_email = models.EmailField(blank=True, null=True, verbose_name="Email de Contacto")
    contacto_telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono de Contacto")


    def get_absolute_url(self):
            # Esta línea es la clave. Genera la URL para el detalle de esta aseguradora.
            return reverse('polizas:detalle_aseguradora', kwargs={'pk': self.pk})

    def __str__(self):
            return self.nombre

    class Meta:
        verbose_name = "Aseguradora"
        verbose_name_plural = "Aseguradoras"
        ordering = ['nombre']
        unique_together = ('usuario', 'nombre')
        unique_together = ('usuario', 'rif')

# ---  MODELO PARA CADA PERSONA CUBIERTA EN LA PÓLIZA ---
class Asegurado(models.Model):

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]

    PARENTESCO_CHOICES = [
        ('TITULAR', 'Titular'),
        ('CONYUGE', 'Cónyuge'),
        ('HIJO_A', 'Hijo/a'),
        ('PADRE_MADRE', 'Padre/Madre'),
        ('OTRO', 'Otro'),
    ]

    poliza = models.ForeignKey('Poliza', on_delete=models.CASCADE, related_name='asegurados')

    # --- CAMPOS MODIFICADOS PARA SER OPCIONALES ---
    nombre_completo = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nombre Completo del Asegurado")
    cedula = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cédula / RIF")
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name="Fecha de Nacimiento")
    parentesco = models.CharField(max_length=20, choices=PARENTESCO_CHOICES, blank=True, null=True) # <-- AÑADIR blank=True, null=True
    
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True, null=True, verbose_name="Sexo")
    email = models.EmailField(blank=True, null=True, verbose_name="Email del Asegurado")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono del Asegurado")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas sobre el Asegurado")
    # Aquí podríamos añadir más campos específicos
    # para cada asegurado individual.

    def __str__(self):
        return f"{self.nombre_completo} ({self.get_parentesco_display()}) en Póliza {self.poliza.numero_poliza}"

    class Meta:
        verbose_name = "Asegurado en Póliza"
        verbose_name_plural = "Asegurados en Póliza"
        ordering = ['parentesco', 'nombre_completo']

class Poliza(models.Model):

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='polizas')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="polizas_contratadas", verbose_name="Cliente Contratante/Tomador")

# --- NUEVO CAMPO PARA ENLAZAR RENOVACIONES ---
    # `self` significa que la relación es con el mismo modelo.
    # `on_delete=models.SET_NULL` por si la póliza original se borra, no perder la renovación.
    renovacion_de = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='renovaciones',
        verbose_name="Es renovación de"
    )


    FRECUENCIA_PAGO_CHOICES = [
        ('UNICO', 'Pago Único'), # Volvemos a un nombre más claro
        ('MENSUAL', 'Mensual'),
        ('TRIMESTRAL', 'Trimestral'),
        ('CUATRIMESTRAL', 'Cuatrimestral'),
        ('SEMESTRAL', 'Semestral'),
        ('ANUAL', 'Anual'), # Anual es lo mismo que Pago Único en términos de cuotas
    ]

    ESTADO_POLIZA_CHOICES = [
        ('VIGENTE', 'Vigente'),
        ('PENDIENTE_PAGO', 'Pendiente de Pago'), # Este estado ahora se refiere al pago inicial
        ('VENCIDA', 'Vencida'),
        ('CANCELADA', 'Cancelada'),
        ('EN_TRAMITE', 'En Trámite'),
        ('RENOVADA', 'Renovada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="polizas", verbose_name="Cliente")
    aseguradora = models.ForeignKey(Aseguradora, on_delete=models.SET_NULL, null=True, blank=True, related_name="polizas", verbose_name="Aseguradora")
    numero_poliza = models.CharField(max_length=100, unique=True, verbose_name="Número de Póliza")
    ramo_tipo_seguro = models.CharField(max_length=100, verbose_name="Ramo o Tipo de Seguro (Ej: Vida, Auto, Hogar)")
    descripcion_bien_asegurado = models.TextField(blank=True, null=True, verbose_name="Descripción del Bien Asegurado (Ej: Placa Vehículo, Dirección Inmueble)")

    fecha_emision = models.DateField(default=timezone.now, verbose_name="Fecha de Emisión")
    fecha_inicio_vigencia = models.DateField(verbose_name="Fecha Inicio de Vigencia")
    fecha_fin_vigencia = models.DateField(verbose_name="Fecha Fin de Vigencia")

    prima_total_anual = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Prima Total Anual/Valor Asegurado")
    frecuencia_pago = models.CharField(max_length=15, choices=FRECUENCIA_PAGO_CHOICES, default='ANUAL', verbose_name="Frecuencia de Pago de Cuotas")
    valor_cuota = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Valor Cuota (si aplica)")

    comision_monto = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Monto de Comisión")
    comision_cobrada = models.BooleanField(default=False, verbose_name="¿Comisión Cobrada?")
    fecha_cobro_comision = models.DateField(null=True, blank=True, verbose_name="Fecha Cobro Comisión")

    estado_poliza = models.CharField(max_length=20, choices=ESTADO_POLIZA_CHOICES, default='EN_TRAMITE', verbose_name="Estado de la Póliza")
    notas_poliza = models.TextField(blank=True, null=True, verbose_name="Notas Adicionales de la Póliza")

    # Campo para el archivo de la póliza (opcional)
    archivo_poliza = models.FileField(upload_to='polizas_archivos/', blank=True, null=True, verbose_name="Archivo de la Póliza (PDF)")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    documentos = GenericRelation(Documento)
    
    # --- PROPIEDADES PARA RENOVACIÓN ---

    @property
    def dias_para_renovar(self):
        hoy = timezone.now().date()
        if self.fecha_fin_vigencia:
            # Si el estado no implica una vigencia activa, no calculamos días.
            # 'VIGENTE' es el único estado que garantiza que la póliza está activa y corriendo.
            if self.estado_poliza != 'VIGENTE':
                return None
            
            delta = self.fecha_fin_vigencia - hoy
            return delta.days
        return None

    @property
    def estado_renovacion(self):
        """
        Determina el estado de renovación basado en una jerarquía de prioridades:
        1. Estados administrativos finales (Renovada, Cancelada).
        2. Estados que requieren acción (En Trámite, Pendiente de Pago).
        3. Estados basados en la fecha de vencimiento (Vencida, Crítico, Próximo, Vigente).
        """
        # Prioridad 1: Estados finales que no requieren más seguimiento de renovación.
        if self.estado_poliza == 'RENOVADA':
            return "Renovada"
        if self.estado_poliza == 'CANCELADA':
            return "Cancelada"

        # Prioridad 2: Estados que requieren una acción para activarse.
        if self.estado_poliza == 'EN_TRAMITE':
            return "En Trámite"
        if self.estado_poliza == 'PENDIENTE_PAGO':
            return "Pendiente de Pago"

        # Prioridad 3: Si no es ninguno de los anteriores, calculamos por fecha.
        dias = self.dias_para_renovar
        
        # Si 'dias' es None, significa que la póliza no está 'VIGENTE'.
        # Podría estar 'VENCIDA' según su estado administrativo.
        if dias is None:
            # Comprobamos si la fecha ya pasó para marcarla como vencida
            # incluso si su estado administrativo aún no se ha actualizado.
            if self.fecha_fin_vigencia and self.fecha_fin_vigencia < timezone.now().date():
                return "Vencida"
            return "Indeterminado" # Caso raro, no debería ocurrir

        if dias < 0:
            return "Vencida"
        elif dias <= 30:
            return "Crítico (0-30 días)"
        elif dias <= 90:
            return "Próximo (31-90 días)"
        else: # Más de 90 días
            return "Vigente"

    @property
    def proxima_fecha_renovacion_calculada(self):
        # Esta es una lógica simple, asume que se renueva al día siguiente del fin de vigencia
        # y la nueva vigencia sería por el mismo periodo de la frecuencia
        if not self.fecha_fin_vigencia or not self.frecuencia_pago:
            return None

        # La fecha base para la próxima renovación es el día después del fin de vigencia actual
        base_renovacion = self.fecha_fin_vigencia + relativedelta(days=1)

        if self.frecuencia_pago == 'MENSUAL':
            return base_renovacion + relativedelta(months=1) - relativedelta(days=1)
        elif self.frecuencia_pago == 'TRIMESTRAL':
            return base_renovacion + relativedelta(months=3) - relativedelta(days=1)
        elif self.frecuencia_pago == 'CUATRIMESTRAL':
            return base_renovacion + relativedelta(months=4) - relativedelta(days=1)
        elif self.frecuencia_pago == 'SEMESTRAL':
            return base_renovacion + relativedelta(months=6) - relativedelta(days=1)
        elif self.frecuencia_pago == 'ANUAL' or self.frecuencia_pago == 'UNICO': # 'UNICO' podría tratarse como anual para renovación
            return base_renovacion + relativedelta(years=1) - relativedelta(days=1)
        return None # Si la frecuencia no coincide

    # --- PROPIEDAD PARA LA PRÓXIMA FECHA DE COBRO ---

    @property
    def proxima_cuota_pendiente(self):
        return self.cuotas.filter(estado='PENDIENTE').order_by('fecha_vencimiento_cuota').first()

    @property
    def dias_para_proximo_cobro(self):
        proxima_cuota = self.proxima_cuota_pendiente
        if proxima_cuota:
            return (proxima_cuota.fecha_vencimiento_cuota - timezone.now().date()).days
        return None
    
    def generar_plan_de_pagos(self):
        self.cuotas.all().delete()
        if not self.fecha_inicio_vigencia or not self.frecuencia_pago: return

        periodos = {
            'MENSUAL': (relativedelta(months=1), 12), 'TRIMESTRAL': (relativedelta(months=3), 4),
            'CUATRIMESTRAL': (relativedelta(months=4), 3), 'SEMESTRAL': (relativedelta(months=6), 2),
            'ANUAL': (relativedelta(years=1), 1), 'UNICO': (relativedelta(years=1), 1),
        }
        if self.frecuencia_pago not in periodos: return

        periodo, num_cuotas = periodos[self.frecuencia_pago]
        monto_por_cuota = self.valor_cuota if self.valor_cuota and self.valor_cuota > 0 else (self.prima_total_anual / num_cuotas)
        fecha_actual_cuota = self.fecha_inicio_vigencia

        for _ in range(num_cuotas):
            if self.fecha_fin_vigencia and fecha_actual_cuota > self.fecha_fin_vigencia: break
            PagoCuota.objects.create(poliza=self, fecha_vencimiento_cuota=fecha_actual_cuota, monto_cuota=monto_por_cuota)
            fecha_actual_cuota += periodo

    def __str__(self):
        return f"Póliza {self.numero_poliza} - {self.cliente.nombre_completo} ({self.ramo_tipo_seguro})"

    def get_absolute_url(self):
        return reverse('polizas:detalle_poliza', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Póliza"
        verbose_name_plural = "Pólizas"
        ordering = ['-fecha_fin_vigencia', 'cliente']
        # --- RESTRICCIÓN DE UNICIDAD ---
        # Una póliza es única por la combinación de su número, usuario Y fecha de inicio.
        # Esto permite tener "123" para 2025 y "123" para 2026.
        unique_together = ('usuario', 'numero_poliza', 'fecha_inicio_vigencia')


class PagoCuota(models.Model):
    ESTADO_PAGO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('VENCIDO', 'Vencido'), # Opcional, para lógica futura
    ]

    poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE, related_name='cuotas')
    
    fecha_vencimiento_cuota = models.DateField(verbose_name="Fecha de Vencimiento de la Cuota")
    monto_cuota = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto de la Cuota")
    estado = models.CharField(max_length=10, choices=ESTADO_PAGO_CHOICES, default='PENDIENTE')

    # Campos para registrar el pago EFECTIVO
    fecha_de_pago_realizado = models.DateField(null=True, blank=True, verbose_name="Fecha en que se pagó")
    notas_pago = models.TextField(blank=True, null=True, verbose_name="Notas del pago")

    def __str__(self):
        return f"Cuota de {self.poliza.numero_poliza} con vencimiento {self.fecha_vencimiento_cuota}"

    class Meta:
        verbose_name = "Cuota de Póliza"
        verbose_name_plural = "Cuotas de Póliza"
        ordering = ['fecha_vencimiento_cuota']

class Siniestro(models.Model):
    ESTADO_CHOICES = [
        ('REPORTADO', 'Reportado'),
        ('EN_ANALISIS', 'En Análisis'),
        ('PERDIDA_TOTAL', 'Pérdida Total'),
        ('PAGADO', 'Pagado / Indemnizado'),
        ('RECHAZADO', 'Rechazado'),
        ('CERRADO', 'Cerrado'),
    ]

    poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE, related_name='siniestros')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='siniestros')
    
    fecha_ocurrencia = models.DateField(verbose_name="Fecha de Ocurrencia")
    fecha_reporte = models.DateField(default=timezone.now, verbose_name="Fecha de Reporte")
    
    estado_siniestro = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='REPORTADO', verbose_name="Estado del Siniestro")
    descripcion = models.TextField(verbose_name="Descripción del Siniestro")
    
    monto_reclamado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Monto Reclamado")
    monto_indemnizado = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Monto Indemnizado/Pagado")

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    documentos = GenericRelation(Documento)


    def __str__(self):
        return f"Siniestro para Póliza {self.poliza.numero_poliza} ({self.fecha_ocurrencia})"
        
    def get_absolute_url(self):
        return reverse('polizas:detalle_siniestro', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Siniestro"
        verbose_name_plural = "Siniestros"
        ordering = ['-fecha_ocurrencia']

# ---  FIN DE MODELOS PARA PÓLIZAS DE SEGUROS  ---