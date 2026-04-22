from django.contrib import admin
from django.utils.html import format_html
from .models import Cliente, Conductor, Vehiculo, Reservacion, Pago


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "telefono",
        "correo",
        "reservas_count",
        "activo",
        "creado",
    )
    list_display_links = ("id", "nombre")
    search_fields = ("nombre", "telefono", "correo")
    list_filter = ("activo", "creado")
    readonly_fields = ("creado", "reservas_count", "reservas_activas")
    fieldsets = (
        (
            "Información Personal",
            {"fields": ("usuario", "nombre", "telefono", "correo", "direccion")},
        ),
        ("Estadísticas", {"fields": ("reservas_count", "reservas_activas", "creado")}),
        ("Estado", {"fields": ("activo",)}),
    )

    def reservas_count(self, obj):
        return obj.reservas_count

    reservas_count.short_description = "Total Reservas"


@admin.register(Conductor)
class ConductorAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "telefono",
        "licencia",
        "edad",
        "disponible",
        "activo",
        "creado",
    )
    list_display_links = ("id", "nombre")
    list_filter = ("disponible", "activo", "creado")
    search_fields = ("nombre", "licencia", "telefono")
    readonly_fields = ("creado", "edad")
    fieldsets = (
        (
            "Información Personal",
            {
                "fields": (
                    "nombre",
                    "telefono",
                    "licencia",
                    "fecha_nacimiento",
                    "experiencia_años",
                )
            },
        ),
        ("Estado", {"fields": ("disponible", "activo", "creado")}),
    )

    def edad(self, obj):
        return obj.edad

    edad.short_description = "Edad"


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "placa",
        "marca",
        "modelo",
        "año",
        "tipo",
        "capacidad",
        "conductor",
        "necesita_mantenimiento",
        "activo",
    )
    list_display_links = ("id", "placa")
    search_fields = ("placa", "modelo", "marca")
    list_filter = ("tipo", "capacidad", "activo", "año")
    readonly_fields = ("creado", "necesita_mantenimiento", "conductor_nombre")
    fieldsets = (
        (
            "Información del Vehículo",
            {"fields": ("placa", "marca", "modelo", "año", "tipo", "capacidad")},
        ),
        ("Asignación", {"fields": ("conductor", "conductor_nombre")}),
        (
            "Mantenimiento",
            {"fields": ("mantenimiento_proximo", "necesita_mantenimiento")},
        ),
        ("Estado", {"fields": ("activo", "creado")}),
    )

    def necesita_mantenimiento(self, obj):
        if obj.necesita_mantenimiento:
            return format_html('<span style="color: red;">⚠️ Necesita</span>')
        return format_html('<span style="color: green;">✅ OK</span>')

    necesita_mantenimiento.short_description = "Mantenimiento"


@admin.register(Reservacion)
class ReservacionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cliente",
        "conductor",
        "vehiculo",
        "origen",
        "destino",
        "fecha_viaje",
        "monto",
        "estado_badge",
        "creado",
    )
    list_display_links = ("id", "cliente")
    list_filter = ("estado", "fecha_viaje", "creado")
    search_fields = (
        "cliente__nombre",
        "conductor__nombre",
        "origen",
        "destino",
    )
    readonly_fields = ("fecha_reserva", "creado", "duracion_viaje", "tiene_pago")
    autocomplete_fields = ("cliente", "conductor", "vehiculo")
    fieldsets = (
        ("Información de Reserva", {"fields": ("cliente", "conductor", "vehiculo")}),
        (
            "Detalles del Viaje",
            {
                "fields": (
                    "origen",
                    "destino",
                    "fecha_viaje",
                    "fecha_fin_viaje",
                    "distancia_km",
                    "notas",
                )
            },
        ),
        ("Pago", {"fields": ("monto", "tiene_pago")}),
        ("Estado", {"fields": ("estado", "fecha_reserva", "creado", "duracion_viaje")}),
    )

    def estado_badge(self, obj):
        color_map = {
            "pendiente": "orange",
            "confirmada": "blue",
            "en_progreso": "purple",
            "completada": "green",
            "cancelada": "red",
        }
        color = color_map.get(obj.estado, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color,
            obj.get_estado_display(),
        )

    estado_badge.short_description = "Estado"


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "reservacion",
        "cliente",
        "monto",
        "metodo",
        "estado_badge",
        "pagado",
        "fecha_pago",
    )
    list_display_links = ("id", "reservacion")
    list_filter = ("metodo", "estado_pago", "pagado", "fecha_pago")
    search_fields = ("reservacion__id", "referencia", "reservacion__cliente__nombre")
    readonly_fields = ("creado", "cliente_nombre")
    fieldsets = (
        (
            "Información del Pago",
            {
                "fields": (
                    "reservacion",
                    "cliente_nombre",
                    "monto",
                    "metodo",
                    "referencia",
                )
            },
        ),
        (
            "Estado del Pago",
            {"fields": ("estado_pago", "pagado", "fecha_pago", "creado")},
        ),
    )

    def cliente(self, obj):
        return obj.reservacion.cliente.nombre

    cliente.short_description = "Cliente"

    def estado_badge(self, obj):
        color_map = {
            "pendiente": "orange",
            "procesando": "blue",
            "completado": "green",
            "fallido": "red",
            "reembolsado": "gray",
        }
        color = color_map.get(obj.estado_pago, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color,
            obj.get_estado_pago_display(),
        )

    estado_badge.short_description = "Estado"
