from rest_framework import serializers
from .models import Cliente, Conductor, Vehiculo, Reservacion, Pago
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class ClienteSerializer(serializers.ModelSerializer):
    usuario_info = UserSerializer(source="usuario", read_only=True)
    reservas_count = serializers.ReadOnlyField()
    reservas_activas = serializers.ReadOnlyField()

    class Meta:
        model = Cliente
        fields = [
            "id",
            "usuario",
            "usuario_info",
            "nombre",
            "telefono",
            "correo",
            "direccion",
            "creado",
            "activo",
            "reservas_count",
            "reservas_activas",
        ]
        read_only_fields = ["creado"]


class ConductorSerializer(serializers.ModelSerializer):
    edad = serializers.ReadOnlyField()
    vehiculo_placa = serializers.CharField(source="vehiculo.placa", read_only=True)

    class Meta:
        model = Conductor
        fields = [
            "id",
            "nombre",
            "telefono",
            "licencia",
            "disponible",
            "creado",
            "activo",
            "fecha_nacimiento",
            "experiencia_años",
            "edad",
            "vehiculo_placa",
        ]
        read_only_fields = ["creado"]


class VehiculoSerializer(serializers.ModelSerializer):
    conductor_nombre = serializers.CharField(source="conductor.nombre", read_only=True)
    necesita_mantenimiento = serializers.ReadOnlyField()

    class Meta:
        model = Vehiculo
        fields = [
            "id",
            "placa",
            "marca",
            "modelo",
            "año",
            "tipo",
            "capacidad",
            "conductor",
            "conductor_nombre",
            "activo",
            "creado",
            "mantenimiento_proximo",
            "necesita_mantenimiento",
        ]
        read_only_fields = ["creado"]


class ReservacionSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)
    conductor_nombre = serializers.CharField(source="conductor.nombre", read_only=True)
    vehiculo_placa = serializers.CharField(source="vehiculo.placa", read_only=True)
    duracion_viaje = serializers.ReadOnlyField()
    tiene_pago = serializers.ReadOnlyField()

    # Campos para crear nuevo cliente
    crear_nuevo_cliente = serializers.BooleanField(write_only=True, required=False)
    nuevo_cliente_nombre = serializers.CharField(
        write_only=True, required=False, max_length=120
    )
    nuevo_cliente_telefono = serializers.CharField(
        write_only=True, required=False, max_length=20
    )
    nuevo_cliente_correo = serializers.EmailField(write_only=True, required=False)
    nuevo_cliente_direccion = serializers.CharField(
        write_only=True, required=False, max_length=255
    )

    class Meta:
        model = Reservacion
        fields = [
            "id",
            "cliente",
            "cliente_nombre",
            "conductor",
            "conductor_nombre",
            "vehiculo",
            "vehiculo_placa",
            "origen",
            "destino",
            "notas",
            "fecha_reserva",
            "fecha_viaje",
            "fecha_fin_viaje",
            "monto",
            "distancia_km",
            "estado",
            "creado",
            "duracion_viaje",
            "tiene_pago",
            # Campos para nuevo cliente
            "crear_nuevo_cliente",
            "nuevo_cliente_nombre",
            "nuevo_cliente_telefono",
            "nuevo_cliente_correo",
            "nuevo_cliente_direccion",
        ]
        read_only_fields = ["fecha_reserva", "creado"]

    def create(self, validated_data):
        # Extraer datos del nuevo cliente si se proporcionan
        crear_nuevo_cliente = validated_data.pop("crear_nuevo_cliente", False)
        nuevo_cliente_data = {}

        if crear_nuevo_cliente:
            for field in [
                "nuevo_cliente_nombre",
                "nuevo_cliente_telefono",
                "nuevo_cliente_correo",
                "nuevo_cliente_direccion",
            ]:
                if field in validated_data:
                    field_name = field.replace("nuevo_cliente_", "")
                    nuevo_cliente_data[field_name] = validated_data.pop(field)

        # Crear reservación
        reservacion = Reservacion.objects.create(**validated_data)

        # Crear nuevo cliente si es necesario
        if crear_nuevo_cliente and nuevo_cliente_data:
            cliente = Cliente.objects.create(**nuevo_cliente_data)
            reservacion.cliente = cliente
            reservacion.save()

            # Crear pago automáticamente
            Pago.objects.create(
                reservacion=reservacion,
                monto=reservacion.monto,
                metodo="efectivo",
                estado_pago="pendiente",
            )

        return reservacion


class PagoSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(
        source="reservacion.cliente.nombre", read_only=True
    )
    reservacion_id = serializers.IntegerField(source="reservacion.id", read_only=True)

    class Meta:
        model = Pago
        fields = [
            "id",
            "reservacion",
            "reservacion_id",
            "monto",
            "metodo",
            "estado_pago",
            "pagado",
            "fecha_pago",
            "creado",
            "referencia",
            "cliente_nombre",
        ]
        read_only_fields = ["creado", "pagado"]


class DashboardStatsSerializer(serializers.Serializer):
    total_reservas = serializers.IntegerField()
    total_clientes = serializers.IntegerField()
    total_conductores = serializers.IntegerField()
    total_vehiculos = serializers.IntegerField()
    total_confirmadas = serializers.IntegerField()
    total_canceladas = serializers.IntegerField()
    total_pendientes = serializers.IntegerField()
    total_ganancias = serializers.DecimalField(max_digits=12, decimal_places=2)
    reservas_por_mes = serializers.ListField()
    conductores_disponibles = serializers.IntegerField()
    vehiculos_mantenimiento = serializers.IntegerField()
