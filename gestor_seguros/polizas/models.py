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

    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre Completo del Asegurado")
    cedula = models.CharField(max_length=20, blank=True, null=True, verbose_name="Cédula / RIF")
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name="Fecha de Nacimiento")
    parentesco = models.CharField(max_length=20, choices=PARENTESCO_CHOICES, default='TITULAR')
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
        # --- PASO 1: Priorizar el estado administrativo de la póliza ---
        # Si la póliza requiere una acción para activarse, ese es su estado principal.
        if self.estado_poliza in ['EN_TRAMITE', 'PENDIENTE_PAGO']:
            return "Pendiente Activación"
        
        # Si la póliza ya fue gestionada (cerrada), mostramos su estado final.
        if self.estado_poliza in ['RENOVADA', 'CANCELADA']:
            return "Gestionada"
        
        # Si el estado es 'VENCIDA', ese es su estado final de renovación.
        if self.estado_poliza == 'VENCIDA':
            return "Vencida"

        # --- PASO 2: Si la póliza está VIGENTE, ahora sí calculamos por fecha ---
        # Si llegamos aquí, la única opción que queda es que self.estado_poliza == 'VIGENTE'
        
        dias = self.dias_para_renovar

        if dias is None:
            # Esto no debería pasar si la póliza es VIGENTE, pero es una salvaguarda.
            return "Indeterminado"

        if dias < 0:
            # Doble chequeo. Si está marcada como VIGENTE pero su fecha ya pasó.
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
    def proxima_fecha_cobro(self):
        # Casos base donde no hay "próximo cobro periódico"
        if not self.fecha_inicio_vigencia or self.frecuencia_pago in ['UNICO', 'ANUAL']:
            hoy = timezone.now().date()
            # Si es pago único/anual y no se ha pagado, el cobro es la fecha de inicio
            if hoy <= self.fecha_fin_vigencia and not self.pagos_cuotas.exists():
                return self.fecha_inicio_vigencia
            return None

        # --- Lógica Avanzada para Cuotas Periódicas ---
        periodos = {
            'MENSUAL': relativedelta(months=1),
            'TRIMESTRAL': relativedelta(months=3),
            'CUATRIMESTRAL': relativedelta(months=4),
            'SEMESTRAL': relativedelta(months=6),
        }
        periodo = periodos.get(self.frecuencia_pago)
        if not periodo: return None

        # 1. Obtenemos la última fecha de cuota que fue pagada.
        # Si no hay pagos, la base es la fecha de inicio de la póliza.
        ultimo_pago = self.pagos_cuotas.order_by('-fecha_cuota_correspondiente').first()
        fecha_base_ultimo_pago = ultimo_pago.fecha_cuota_correspondiente if ultimo_pago else None

        # La primera cuota teórica es siempre la fecha de inicio de vigencia.
        primera_cuota_teorica = self.fecha_inicio_vigencia

        # Si no hay pagos, la próxima cuota es la primera.
        if not fecha_base_ultimo_pago:
            # Comprobamos que la primera cuota no exceda el fin de vigencia
            if self.fecha_fin_vigencia and primera_cuota_teorica > self.fecha_fin_vigencia:
                return None
            return primera_cuota_teorica
        
        # Si ya hay pagos, calculamos la siguiente cuota teórica a partir del último pago.
        siguiente_cuota_teorica = fecha_base_ultimo_pago + periodo
        
        # Verificamos que esta siguiente cuota no se pase del fin de la vigencia.
        # El <= es importante para incluir la cuota que cae justo en la fecha de fin.
        if self.fecha_fin_vigencia and siguiente_cuota_teorica <= self.fecha_fin_vigencia:
            return siguiente_cuota_teorica
        
        # Si la siguiente cuota se pasa, significa que ya no hay más cuotas que pagar.
        return None


    @property
    def dias_para_proximo_cobro(self):
        if self.proxima_fecha_cobro:
            hoy = timezone.now().date()
            delta = self.proxima_fecha_cobro - hoy
            return delta.days
        return None

    def __str__(self):
        return f"Póliza {self.numero_poliza} - {self.cliente.nombre_completo} ({self.ramo_tipo_seguro})"

    def get_absolute_url(self):
        return reverse('polizas:detalle_poliza', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = "Póliza"
        verbose_name_plural = "Pólizas"
        ordering = ['-fecha_fin_vigencia', 'cliente']
        unique_together = ('usuario', 'numero_poliza')

class PagoCuota(models.Model):
    poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE, related_name='pagos_cuotas')
    fecha_pago = models.DateField(default=timezone.now, verbose_name="Fecha en que se realizó el pago")
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto Pagado")
    fecha_cuota_correspondiente = models.DateField(verbose_name="Cuota correspondiente a la fecha")
    notas = models.TextField(blank=True, null=True, verbose_name="Notas del pago")

    def __str__(self):
        return f"Pago de ${self.monto_pagado} para póliza {self.poliza.numero_poliza} el {self.fecha_pago}"

    class Meta:
        verbose_name = "Pago de Cuota"
        verbose_name_plural = "Pagos de Cuotas"
        ordering = ['-fecha_cuota_correspondiente']

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

