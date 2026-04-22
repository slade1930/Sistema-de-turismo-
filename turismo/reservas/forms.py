from django import forms
from .models import Reservacion, Cliente, Conductor, Vehiculo, Pago
from django.utils import timezone


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "telefono", "correo", "direccion"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre completo",
                }
            ),
            "telefono": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Teléfono",
                }
            ),
            "correo": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Correo electrónico",
                }
            ),
            "direccion": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Dirección (opcional)"}
            ),
        }


class ConductorForm(forms.ModelForm):
    class Meta:
        model = Conductor
        fields = [
            "nombre",
            "telefono",
            "licencia",
            "fecha_nacimiento",
            "experiencia_años",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "licencia": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_nacimiento": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "experiencia_años": forms.NumberInput(attrs={"class": "form-control"}),
        }


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = [
            "placa",
            "marca",
            "modelo",
            "año",
            "tipo",
            "capacidad",
            "conductor",
            "mantenimiento_proximo",
        ]
        widgets = {
            "placa": forms.TextInput(attrs={"class": "form-control"}),
            "marca": forms.TextInput(attrs={"class": "form-control"}),
            "modelo": forms.TextInput(attrs={"class": "form-control"}),
            "año": forms.NumberInput(attrs={"class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-control"}),
            "capacidad": forms.NumberInput(attrs={"class": "form-control"}),
            "conductor": forms.Select(attrs={"class": "form-control"}),
            "mantenimiento_proximo": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }


class ReservaForm(forms.ModelForm):
    crear_nuevo_cliente = forms.BooleanField(
        required=False, initial=False, label="Crear nuevo cliente"
    )

    nuevo_cliente_nombre = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nombre del nuevo cliente"}
        ),
    )

    nuevo_cliente_telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Teléfono"}
        ),
    )

    nuevo_cliente_correo = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Correo electrónico"}
        ),
    )

    nuevo_cliente_direccion = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Dirección"}
        ),
    )

    class Meta:
        model = Reservacion
        fields = [
            "cliente",
            "conductor",
            "vehiculo",
            "origen",
            "destino",
            "fecha_viaje",
            "monto",
            "distancia_km",
            "notas",
            "estado",
        ]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-control"}),
            "conductor": forms.Select(attrs={"class": "form-control"}),
            "vehiculo": forms.Select(attrs={"class": "form-control"}),
            "origen": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Dirección de origen",
                }
            ),
            "destino": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Dirección de destino",
                }
            ),
            "fecha_viaje": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "monto": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "distancia_km": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "notas": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "estado": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar conductores y vehículos disponibles
        self.fields["conductor"].queryset = Conductor.objects.filter(
            disponible=True, activo=True
        )
        self.fields["vehiculo"].queryset = Vehiculo.objects.filter(activo=True)

        # Establecer fecha mínima para el viaje (hoy)
        self.fields["fecha_viaje"].widget.attrs["min"] = timezone.now().strftime(
            "%Y-%m-%dT%H:%M"
        )


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ["monto", "metodo", "estado_pago", "referencia"]
        widgets = {
            "monto": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "metodo": forms.Select(attrs={"class": "form-control"}),
            "estado_pago": forms.Select(attrs={"class": "form-control"}),
            "referencia": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Referencia de pago"}
            ),
        }
