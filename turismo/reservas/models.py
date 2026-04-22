from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator
from django.utils import timezone


# ✅ CLIENTE
class Cliente(models.Model):
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Usuario del sistema opcionalmente vinculado",
    )
    nombre = models.CharField(max_length=120)
    telefono = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="El número de teléfono debe tener entre 9 y 15 dígitos.",
            )
        ],
    )
    correo = models.EmailField(unique=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.nombre} ({self.correo})"

    @property
    def reservas_count(self):
        return self.reservacion_set.count()

    @property
    def reservas_activas(self):
        return self.reservacion_set.filter(
            estado__in=["pendiente", "en_progreso"]
        ).count()


# ✅ CONDUCTOR
class Conductor(models.Model):
    nombre = models.CharField(max_length=120)
    telefono = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message="El número de teléfono debe tener entre 9 y 15 dígitos.",
            )
        ],
    )
    licencia = models.CharField(max_length=50, unique=True)
    disponible = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    experiencia_años = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Conductor"
        verbose_name_plural = "Conductores"
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.nombre} - {self.licencia} - {'✅ Disponible' if self.disponible else '❌ Ocupado'}"

    @property
    def edad(self):
        if self.fecha_nacimiento:
            today = timezone.now().date()
            return (
                today.year
                - self.fecha_nacimiento.year
                - (
                    (today.month, today.day)
                    < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
                )
            )
        return None


# ✅ VEHÍCULO
class Vehiculo(models.Model):
    TIPO_VEHICULO = [
        ("sedan", "Sedán"),
        ("suv", "SUV"),
        ("van", "Van"),
        ("camioneta", "Camioneta"),
    ]

    placa = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z0-9-]{4,10}$", message="Formato de placa inválido."
            )
        ],
    )
    modelo = models.CharField(max_length=100)
    marca = models.CharField(max_length=50, default="Generica")
    año = models.PositiveIntegerField(
        default=2020, validators=[MinValueValidator(1990)]
    )
    tipo = models.CharField(max_length=20, choices=TIPO_VEHICULO, default="sedan")
    capacidad = models.PositiveIntegerField(default=4)
    conductor = models.OneToOneField(
        Conductor, on_delete=models.SET_NULL, null=True, blank=True
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    mantenimiento_proximo = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo} ({self.año})"

    @property
    def necesita_mantenimiento(self):
        if self.mantenimiento_proximo:
            return self.mantenimiento_proximo <= timezone.now().date()
        return False

    @property
    def conductor_nombre(self):
        return self.conductor.nombre if self.conductor else "Sin conductor"


# ✅ RESERVACIÓN
class Reservacion(models.Model):
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("confirmada", "Confirmada"),
        ("en_progreso", "En progreso"),
        ("completada", "Completada"),
        ("cancelada", "Cancelada"),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    conductor = models.ForeignKey(
        Conductor, on_delete=models.SET_NULL, null=True, blank=True
    )
    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.SET_NULL, null=True, blank=True
    )

    origen = models.CharField(max_length=255)
    destino = models.CharField(max_length=255)
    notas = models.TextField(
        blank=True, null=True, help_text="Notas adicionales para la reserva"
    )

    fecha_reserva = models.DateTimeField(auto_now_add=True)
    fecha_viaje = models.DateTimeField(null=True, blank=True)
    fecha_fin_viaje = models.DateTimeField(null=True, blank=True)

    monto = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    distancia_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendiente")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reservación"
        verbose_name_plural = "Reservaciones"
        ordering = ["-creado", "-fecha_viaje"]

    def __str__(self):
        return (
            f"Reserva #{self.id} - {self.cliente.nombre} - {self.get_estado_display()}"
        )

    def save(self, *args, **kwargs):
        # Si se asigna un conductor, marcarlo como no disponible
        if self.conductor and self.estado in ["confirmada", "en_progreso"]:
            self.conductor.disponible = False
            self.conductor.save()

        # Si se completa o cancela la reserva, liberar conductor
        if self.estado in ["completada", "cancelada"] and self.conductor:
            self.conductor.disponible = True
            self.conductor.save()

        super().save(*args, **kwargs)

    @property
    def duracion_viaje(self):
        if self.fecha_viaje and self.fecha_fin_viaje:
            return self.fecha_fin_viaje - self.fecha_viaje
        return None

    @property
    def tiene_pago(self):
        return hasattr(self, "pago")


# ✅ PAGO
class Pago(models.Model):
    METODOS_PAGO = [
        ("efectivo", "Efectivo"),
        ("tarjeta", "Tarjeta"),
        ("transferencia", "Transferencia"),
        ("digital", "Pago Digital"),
    ]

    ESTADOS_PAGO = [
        ("pendiente", "Pendiente"),
        ("procesando", "Procesando"),
        ("completado", "Completado"),
        ("fallido", "Fallido"),
        ("reembolsado", "Reembolsado"),
    ]

    reservacion = models.OneToOneField(
        Reservacion, on_delete=models.CASCADE, related_name="pago"
    )
    monto = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    metodo = models.CharField(max_length=20, choices=METODOS_PAGO)
    estado_pago = models.CharField(
        max_length=20, choices=ESTADOS_PAGO, default="pendiente"
    )
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    creado = models.DateTimeField(
        default=timezone.now
    )  # 🔥 SOLO default, NO auto_now_add
    referencia = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-creado"]

    def __str__(self):
        return f"Pago #{self.id} - Reserva {self.reservacion.id} - {self.get_estado_pago_display()}"

    def save(self, *args, **kwargs):
        # Actualizar estado de pagado basado en estado_pago
        self.pagado = self.estado_pago == "completado"

        # Si se marca como completado y no hay fecha de pago, establecerla
        if self.estado_pago == "completado" and not self.fecha_pago:
            self.fecha_pago = timezone.now()

        super().save(*args, **kwargs)

    @property
    def cliente_nombre(self):
        return self.reservacion.cliente.nombre
