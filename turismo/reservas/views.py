from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils.timezone import now, timedelta
from django.db.models.functions import TruncMonth, TruncDay
from django.http import JsonResponse

from .models import Cliente, Conductor, Vehiculo, Reservacion, Pago
from .serializers import (
    ClienteSerializer,
    ConductorSerializer,
    VehiculoSerializer,
    ReservacionSerializer,
    PagoSerializer,
    DashboardStatsSerializer,
)
from .forms import ReservaForm, ClienteForm, ConductorForm, VehiculoForm, PagoForm


# ===========================================
# ✅ PAGINACIÓN PERSONALIZADA
# ===========================================
class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


# ===========================================
# ✅ VISTAS HTML (Templates)
# ===========================================
def home(request):
    return render(request, "index.html")


def dashboard(request):
    # Estadísticas principales
    total_reservas = Reservacion.objects.count()
    total_clientes = Cliente.objects.filter(activo=True).count()
    total_conductores = Conductor.objects.filter(activo=True).count()
    total_vehiculos = Vehiculo.objects.filter(activo=True).count()

    total_confirmadas = Reservacion.objects.filter(estado="completada").count()
    total_canceladas = Reservacion.objects.filter(estado="cancelada").count()
    total_pendientes = Reservacion.objects.filter(
        estado__in=["pendiente", "confirmada"]
    ).count()

    total_ganancias = (
        Pago.objects.filter(estado_pago="completado").aggregate(Sum("monto"))[
            "monto__sum"
        ]
        or 0
    )

    # Reservas por mes para gráfico
    reservas_por_mes = (
        Reservacion.objects.annotate(month=TruncMonth("creado"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    # Estadísticas adicionales - CORREGIDO
    conductores_disponibles = Conductor.objects.filter(
        disponible=True, activo=True
    ).count()

    # Si NO tienes el campo 'mantenimiento_proximo', usa esto:
    # Cambia esto por un campo que SÍ exista en tu modelo Vehiculo
    vehiculos_activos = Vehiculo.objects.filter(activo=True).count()

    # O si quieres mostrar vehículos que necesitan algo específico:
    # Por ejemplo, vehículos con bajo kilometraje o sin conductor
    vehiculos_sin_conductor = Vehiculo.objects.filter(
        activo=True, conductor__isnull=True
    ).count()

    # Reservas recientes
    reservas_recientes = Reservacion.objects.select_related(
        "cliente", "conductor", "vehiculo"
    ).order_by("-creado")[:5]

    # Pagos pendientes
    pagos_pendientes = Pago.objects.filter(estado_pago="pendiente").select_related(
        "reservacion__cliente"
    )[:5]

    context = {
        "total_reservas": total_reservas,
        "total_clientes": total_clientes,
        "total_conductores": total_conductores,
        "total_vehiculos": total_vehiculos,
        "total_confirmadas": total_confirmadas,
        "total_canceladas": total_canceladas,
        "total_pendientes": total_pendientes,
        "total_ganancias": total_ganancias,
        "reservas_por_mes": list(reservas_por_mes),
        "conductores_disponibles": conductores_disponibles,
        "vehiculos_mantenimiento": vehiculos_sin_conductor,  # Cambiado
        "reservas_recientes": reservas_recientes,
        "pagos_pendientes": pagos_pendientes,
    }

    return render(request, "reservas/dashboard.html", context)


def lista_reservas(request):
    query = request.GET.get("q", "")
    estado = request.GET.get("estado", "")

    reservas = Reservacion.objects.select_related(
        "cliente", "conductor", "vehiculo"
    ).order_by("-creado")

    if query:
        reservas = reservas.filter(
            Q(cliente__nombre__icontains=query)
            | Q(origen__icontains=query)
            | Q(destino__icontains=query)
            | Q(conductor__nombre__icontains=query)
        )

    if estado:
        reservas = reservas.filter(estado=estado)

    # Calcular estadísticas para las tarjetas
    total_reservas = reservas.count()
    pendientes = reservas.filter(estado="pendiente").count()
    confirmadas = reservas.filter(estado="confirmada").count()
    en_progreso = reservas.filter(estado="en_progreso").count()
    completadas = reservas.filter(estado="completada").count()
    canceladas = reservas.filter(estado="cancelada").count()

    # Calcular ingresos totales de las reservas completadas
    ingresos_totales = (
        reservas.filter(estado="completada").aggregate(total=Sum("monto"))["total"] or 0
    )

    return render(
        request,
        "reservas/lista_reservas.html",
        {
            "reservas": reservas,
            "query": query,
            "estado": estado,
            "pendientes": pendientes,
            "confirmadas": confirmadas,
            "en_progreso": en_progreso,
            "completadas": completadas,
            "canceladas": canceladas,
            "ingresos_totales": ingresos_totales,
        },
    )


def crear_reserva(request):
    if request.method == "POST":
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save()
            messages.success(request, f"Reserva #{reserva.id} creada exitosamente!")
            return redirect("lista_reservas")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = ReservaForm()

    # AGREGAR CONTEXTO NECESARIO (igual que en crear_cliente)
    # Calcular estadísticas para el sidebar
    from django.utils.timezone import now
    from datetime import datetime

    # Reservas del día actual
    hoy = now().date()
    reservas_hoy = Reservacion.objects.filter(creado__date=hoy).count()

    # Conductores disponibles
    conductores_disponibles = Conductor.objects.filter(
        disponible=True, activo=True
    ).count()

    # Vehículos activos
    vehiculos_activos = Vehiculo.objects.filter(activo=True).count()

    context = {
        "form": form,
        "reservas_hoy": reservas_hoy,
        "conductores_disponibles": conductores_disponibles,
        "vehiculos_activos": vehiculos_activos,
    }

    return render(request, "reservas/crear_reserva.html", context)


def eliminar_reserva(request, id):
    reserva = get_object_or_404(Reservacion, id=id)

    if request.method == "POST":
        reserva_id = reserva.id
        reserva.delete()
        messages.success(request, f"Reserva #{reserva_id} eliminada exitosamente!")
        return redirect("lista_reservas")

    return render(request, "reservas/confirmar_eliminar.html", {"reserva": reserva})


def editar_reserva(request, id):
    reserva = get_object_or_404(Reservacion, id=id)

    if request.method == "POST":
        form = ReservaForm(request.POST, instance=reserva)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Reserva #{reserva.id} actualizada exitosamente!"
            )
            return redirect("lista_reservas")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = ReservaForm(instance=reserva)

    # Agregar estadísticas para el sidebar (opcional)
    from django.utils.timezone import now

    # Reservas del día actual
    hoy = now().date()
    reservas_hoy = Reservacion.objects.filter(creado__date=hoy).count()

    # Conductores disponibles
    conductores_disponibles = Conductor.objects.filter(
        disponible=True, activo=True
    ).count()

    # Vehículos activos
    vehiculos_activos = Vehiculo.objects.filter(activo=True).count()

    context = {
        "form": form,
        "reserva": reserva,
        "reservas_hoy": reservas_hoy,
        "conductores_disponibles": conductores_disponibles,
        "vehiculos_activos": vehiculos_activos,
    }

    return render(request, "reservas/editar_reserva.html", context)


# ===========================================
# ✅ VISTAS PARA CLIENTES, CONDUCTORES, VEHÍCULOS (SIMPLIFICADAS)
# ===========================================
def lista_clientes(request):
    clientes = Cliente.objects.all().order_by("-creado")
    clientes_activos = clientes.filter(activo=True).count()

    # Calcular nuevos clientes este mes
    inicio_mes = now().replace(day=1)
    nuevos_este_mes = Cliente.objects.filter(creado__gte=inicio_mes).count()

    # Calcular clientes con reservas
    clientes_con_reservas = (
        clientes.filter(reservacion__isnull=False).distinct().count()
    )

    # Distribución por nivel de fidelidad (versión simplificada)
    # Primero obtenemos todos los clientes
    todos_clientes = list(clientes)

    # Inicializar contadores
    nuevos = 0
    regulares = 0
    frecuentes = 0
    vip = 0

    # Contar usando la propiedad reservas_count
    for cliente in todos_clientes:
        reservas = cliente.reservas_count
        if reservas == 0:
            nuevos += 1
        elif reservas <= 2:
            regulares += 1
        elif reservas <= 5:
            frecuentes += 1
        else:
            vip += 1

    return render(
        request,
        "clientes/lista_clientes.html",
        {
            "clientes": clientes,
            "clientes_activos": clientes_activos,
            "nuevos_este_mes": nuevos_este_mes,
            "clientes_con_reservas": clientes_con_reservas,
            "nuevos": nuevos,
            "regulares": regulares,
            "frecuentes": frecuentes,
            "vip": vip,
        },
    )


def crear_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(
                request, f"Cliente '{cliente.nombre}' creado exitosamente!"
            )
            return redirect("lista_clientes")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = ClienteForm()

    # Agregar variables al contexto
    total_clientes = Cliente.objects.count()
    clientes_activos = Cliente.objects.filter(activo=True).count()

    # Calcular nuevos clientes este mes
    inicio_mes = now().replace(day=1)
    nuevos_este_mes = Cliente.objects.filter(creado__gte=inicio_mes).count()

    return render(
        request,
        "clientes/crear_cliente.html",
        {
            "form": form,
            "total_clientes": total_clientes,
            "clientes_activos": clientes_activos,
            "nuevos_este_mes": nuevos_este_mes,
        },
    )


def lista_conductores(request):
    conductores = Conductor.objects.all().order_by("-creado")
    conductores_disponibles = conductores.filter(disponible=True, activo=True).count()
    conductores_experiencia = conductores.filter(experiencia_años__gt=2).count()

    return render(
        request,
        "conductores/lista_conductores.html",
        {
            "conductores": conductores,
            "conductores_disponibles": conductores_disponibles,
            "conductores_experiencia": conductores_experiencia,
        },
    )


def crear_conductor(request):
    if request.method == "POST":
        form = ConductorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Conductor creado exitosamente!")
            return redirect("lista_conductores")
    else:
        form = ConductorForm()

    return render(request, "conductores/crear_conductor.html", {"form": form})


def lista_vehiculos(request):
    vehiculos = Vehiculo.objects.all().order_by("-creado")
    vehiculos_activos = vehiculos.filter(activo=True).count()
    vehiculos_mantenimiento = vehiculos.filter(
        mantenimiento_proximo__lte=now().date()
    ).count()

    # Calcular vehículos sin conductor
    sin_conductor = vehiculos.filter(conductor__isnull=True).count()

    # Calcular distribución por tipo
    sedan_count = vehiculos.filter(tipo="sedan").count()
    suv_count = vehiculos.filter(tipo="suv").count()
    van_count = vehiculos.filter(tipo="van").count()
    bus_count = vehiculos.filter(tipo="bus").count()

    return render(
        request,
        "vehiculos/lista_vehiculos.html",
        {
            "vehiculos": vehiculos,
            "vehiculos_activos": vehiculos_activos,
            "vehiculos_mantenimiento": vehiculos_mantenimiento,
            "sin_conductor": sin_conductor,
            "sedan_count": sedan_count,
            "suv_count": suv_count,
            "van_count": van_count,
            "bus_count": bus_count,
        },
    )


def crear_vehiculo(request):
    if request.method == "POST":
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo creado exitosamente!")
            return redirect("lista_vehiculos")
    else:
        form = VehiculoForm()

    # AGREGAR CONTEXTO NECESARIO (igual que en crear_cliente y crear_reserva)
    # Calcular estadísticas para el sidebar
    total_vehiculos = Vehiculo.objects.count()
    vehiculos_activos = Vehiculo.objects.filter(activo=True).count()
    vehiculos_mantenimiento = Vehiculo.objects.filter(
        mantenimiento_proximo__lte=now().date()
    ).count()

    context = {
        "form": form,
        "total_vehiculos": total_vehiculos,
        "vehiculos_activos": vehiculos_activos,
        "vehiculos_mantenimiento": vehiculos_mantenimiento,
    }

    return render(request, "vehiculos/crear_vehiculo.html", context)


# ===========================================
# ✅ API REST MEJORADA
# ===========================================
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by("-creado")
    serializer_class = ClienteSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "telefono", "correo"]
    ordering_fields = ["nombre", "creado", "activo"]

    @action(detail=False, methods=["get"])
    def activos(self, request):
        clientes_activos = self.get_queryset().filter(activo=True)
        page = self.paginate_queryset(clientes_activos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(clientes_activos, many=True)
        return Response(serializer.data)


class ConductorViewSet(viewsets.ModelViewSet):
    queryset = Conductor.objects.all().order_by("-creado")
    serializer_class = ConductorSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "licencia", "telefono"]
    ordering_fields = ["nombre", "disponible", "creado"]

    @action(detail=False, methods=["get"])
    def disponibles(self, request):
        disponibles = self.get_queryset().filter(disponible=True, activo=True)
        serializer = self.get_serializer(disponibles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def toggle_disponibilidad(self, request, pk=None):
        conductor = self.get_object()
        conductor.disponible = not conductor.disponible
        conductor.save()
        status_text = "disponible" if conductor.disponible else "no disponible"
        return Response({"status": f"Conductor marcado como {status_text}"})


class VehiculoViewSet(viewsets.ModelViewSet):
    queryset = Vehiculo.objects.all()
    serializer_class = VehiculoSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["placa", "modelo", "marca"]
    ordering_fields = ["placa", "año", "capacidad", "creado"]

    @action(detail=False, methods=["get"])
    def activos(self, request):
        vehiculos_activos = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(vehiculos_activos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def necesita_mantenimiento(self, request):
        vehiculos_mantenimiento = self.get_queryset().filter(
            mantenimiento_proximo__lte=now().date()
        )
        serializer = self.get_serializer(vehiculos_mantenimiento, many=True)
        return Response(serializer.data)


class ReservacionViewSet(viewsets.ModelViewSet):
    queryset = Reservacion.objects.all().order_by("-creado")
    serializer_class = ReservacionSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["origen", "destino", "cliente__nombre", "conductor__nombre"]
    ordering_fields = ["creado", "fecha_viaje", "monto", "estado"]

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        reservacion = self.get_object()
        reservacion.estado = "confirmada"
        reservacion.save()
        return Response({"status": "Reservación confirmada ✅"})

    @action(detail=True, methods=["post"])
    def iniciar_viaje(self, request, pk=None):
        reservacion = self.get_object()
        reservacion.estado = "en_progreso"
        reservacion.fecha_viaje = now()
        reservacion.save()
        return Response({"status": "Viaje iniciado 🚗"})

    @action(detail=True, methods=["post"])
    def completar(self, request, pk=None):
        reservacion = self.get_object()
        reservacion.estado = "completada"
        reservacion.fecha_fin_viaje = now()
        reservacion.save()
        return Response({"status": "Viaje completado ✅"})

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        reservacion = self.get_object()
        reservacion.estado = "cancelada"
        reservacion.save()
        return Response({"status": "Reservación cancelada ❌"})

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        hoy = now().date()
        inicio_mes = hoy.replace(day=1)

        stats = {
            "total": self.get_queryset().count(),
            "pendientes": self.get_queryset().filter(estado="pendiente").count(),
            "en_progreso": self.get_queryset().filter(estado="en_progresso").count(),
            "completadas_hoy": self.get_queryset()
            .filter(estado="completada", fecha_fin_viaje__date=hoy)
            .count(),
            "ingresos_mes": self.get_queryset()
            .filter(estado="completada", fecha_fin_viaje__date__gte=inicio_mes)
            .aggregate(Sum("monto"))["monto__sum"]
            or 0,
        }

        return Response(stats)


class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all().order_by("-fecha_pago")
    serializer_class = PagoSerializer
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["metodo", "referencia", "reservacion__cliente__nombre"]
    ordering_fields = ["fecha_pago", "monto", "estado_pago"]

    @action(detail=True, methods=["post"])
    def marcar_completado(self, request, pk=None):
        pago = self.get_object()
        pago.estado_pago = "completado"
        pago.save()
        return Response({"status": "Pago marcado como completado ✅"})

    @action(detail=True, methods=["post"])
    def marcar_pendiente(self, request, pk=None):
        pago = self.get_object()
        pago.estado_pago = "pendiente"
        pago.save()
        return Response({"status": "Pago marcado como pendiente ⏳"})

    @action(detail=False, methods=["get"])
    def pendientes(self, request):
        pagos_pendientes = self.get_queryset().filter(estado_pago="pendiente")
        serializer = self.get_serializer(pagos_pendientes, many=True)
        return Response(serializer.data)


@api_view(["GET"])
def dashboard_api(request):
    """API endpoint para datos del dashboard"""
    # Estadísticas principales
    total_reservas = Reservacion.objects.count()
    total_clientes = Cliente.objects.filter(activo=True).count()
    total_conductores = Conductor.objects.filter(activo=True).count()
    total_vehiculos = Vehiculo.objects.filter(activo=True).count()

    total_confirmadas = Reservacion.objects.filter(estado="completada").count()
    total_canceladas = Reservacion.objects.filter(estado="cancelada").count()
    total_pendientes = Reservacion.objects.filter(
        estado__in=["pendiente", "confirmada"]
    ).count()

    total_ganancias = (
        Pago.objects.filter(estado_pago="completado").aggregate(Sum("monto"))[
            "monto__sum"
        ]
        or 0
    )

    # Reservas por mes para gráfico
    reservas_por_mes = list(
        Reservacion.objects.annotate(month=TruncMonth("creado"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    # Estadísticas adicionales
    conductores_disponibles = Conductor.objects.filter(
        disponible=True, activo=True
    ).count()
    vehiculos_mantenimiento = Vehiculo.objects.filter(
        mantenimiento_proximo__lte=now().date()
    ).count()

    data = {
        "total_reservas": total_reservas,
        "total_clientes": total_clientes,
        "total_conductores": total_conductores,
        "total_vehiculos": total_vehiculos,
        "total_confirmadas": total_confirmadas,
        "total_canceladas": total_canceladas,
        "total_pendientes": total_pendientes,
        "total_ganancias": float(total_ganancias),
        "reservas_por_mes": reservas_por_mes,
        "conductores_disponibles": conductores_disponibles,
        "vehiculos_mantenimiento": vehiculos_mantenimiento,
    }

    serializer = DashboardStatsSerializer(data)
    return Response(serializer.data)
