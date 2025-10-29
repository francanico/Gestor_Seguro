# polizas/models.py
from django.db import models
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.conf import settings 
from clientes.models import Cliente 
from dateutil.relativedelta import relativedelta 


class Aseguradora(models.Model):

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='aseguradoras')
    nombre = models.CharField(max_length=150, unique=True, verbose_name="Nombre de la Aseguradora")
    nit = models.CharField(max_length=30, unique=True, blank=True, null=True, verbose_name="NIT")
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

class Poliza(models.Model):

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='polizas')


    FRECUENCIA_PAGO_CHOICES = [
        ('MENSUAL', 'Mensual'),
        ('TRIMESTRAL', 'Trimestral'),
        ('CUATRIMESTRAL', 'Cuatrimestral'),
        ('SEMESTRAL', 'Semestral'),
        ('ANUAL', 'Anual'),
        ('UNICO', 'Pago Único'),
    ]

    ESTADO_POLIZA_CHOICES = [
        ('VIGENTE', 'Vigente'),
        ('PENDIENTE_PAGO', 'Pendiente de Pago'),
        ('VENCIDA', 'Vencida'),
        ('CANCELADA', 'Cancelada'),
        ('EN_TRAMITE', 'En Trámite'),
        ('PAGADA', 'Pagada'),
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
    frecuencia_pago = models.CharField(max_length=15, choices=FRECUENCIA_PAGO_CHOICES, default='ANUAL', verbose_name="Frecuencia de Pago/Renovación")
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

    # --- NUEVO CAMPO PARA PAGOS ADELANTADOS ---
    ultimo_pago_cubierto_hasta = models.DateField(
        null=True, blank=True,
        verbose_name="Último pago cubre hasta",
        help_text="Indica la fecha final del período cubierto por el último pago realizado.")


    @property
    def dias_para_renovar(self):
        hoy = timezone.now().date()
        if self.fecha_fin_vigencia:
            delta = self.fecha_fin_vigencia - hoy
            return delta.days
        return None # O un número muy grande si prefieres

    @property
    def estado_renovacion(self):
        dias = self.dias_para_renovar
        if dias is None:
            return "Indeterminado"
        if dias < 0:
            return "Vencida"
        elif dias <= 30: # Consideramos "Próxima a vencer" 30 días antes
            return "Próxima a vencer"
        else:
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
        if not self.fecha_inicio_vigencia or not self.frecuencia_pago or self.frecuencia_pago == 'UNICO':
            return None

        hoy = timezone.now().date()

        # Si la póliza aún no ha comenzado, el primer cobro es al inicio
        if hoy < self.fecha_inicio_vigencia:
            return self.fecha_inicio_vigencia

        # Mapeo de frecuencia a relativedelta
        periodos = {
            'MENSUAL': relativedelta(months=1),
            'TRIMESTRAL': relativedelta(months=3),
            'CUATRIMESTRAL': relativedelta(months=4),
            'SEMESTRAL': relativedelta(months=6),
            'ANUAL': relativedelta(years=1),
        }
        
        periodo = periodos.get(self.frecuencia_pago)
        if not periodo:
            return None

        # --- Lógica de cálculo robusta ---
        fecha_actual = self.fecha_inicio_vigencia
        
        # Avanzamos la fecha de cobro periodo por periodo hasta que sea mayor o igual a la fecha de hoy
        while fecha_actual < hoy:
            fecha_actual += periodo

        # La fecha encontrada es el próximo cobro.
        # Verificamos que no se pase del final de la vigencia de la póliza.
        if self.fecha_fin_vigencia and fecha_actual > self.fecha_fin_vigencia:
            return None # Ya no hay más cobros dentro de la vigencia
        
        return fecha_actual

    @property
    def dias_para_proximo_cobro(self):
        if self.proxima_fecha_cobro:
            hoy = timezone.now().date()
                # Si hay una fecha de pago adelantado, comparamos contra esa
            if self.ultimo_pago_cubierto_hasta and self.proxima_fecha_cobro <= self.ultimo_pago_cubierto_hasta:
                return None # Ya está cubierto, no hay "días para pagar"
                
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
