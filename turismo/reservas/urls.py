from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"clientes", views.ClienteViewSet)
router.register(r"conductores", views.ConductorViewSet)
router.register(r"vehiculos", views.VehiculoViewSet)
router.register(r"reservaciones", views.ReservacionViewSet)
router.register(r"pagos", views.PagoViewSet)

urlpatterns = [
    # API
    path("api/", include(router.urls)),
    path("api/dashboard/", views.dashboard_api, name="dashboard_api"),
    # Vistas HTML
    path("", views.home, name="home"),
    path("reservas/dash/", views.dashboard, name="dashboard"),
    # Reservas
    path("reservas/", views.lista_reservas, name="lista_reservas"),
    path("reservas/crear/", views.crear_reserva, name="crear_reserva"),
    path("reservas/editar/<int:id>/", views.editar_reserva, name="editar_reserva"),
    path(
        "reservas/eliminar/<int:id>/", views.eliminar_reserva, name="eliminar_reserva"
    ),
    # Clientes
    path("clientes/", views.lista_clientes, name="lista_clientes"),
    path("clientes/crear/", views.crear_cliente, name="crear_cliente"),
    # Conductores
    path("conductores/", views.lista_conductores, name="lista_conductores"),
    path("conductores/crear/", views.crear_conductor, name="crear_conductor"),
    # Vehículos
    path("vehiculos/", views.lista_vehiculos, name="lista_vehiculos"),
    path("vehiculos/crear/", views.crear_vehiculo, name="crear_vehiculo"),
]
