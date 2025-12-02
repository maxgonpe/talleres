from django import forms
from punto_venta.models import CarritoItem, VentaPOS, ConfiguracionPOS, Cotizacion
from core.models import Cliente_Taller


class BuscarRepuestoForm(forms.Form):
    """Formulario para búsqueda rápida de repuestos en POS"""
    busqueda = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Buscar por nombre, SKU, código de barras...',
            'autofocus': True,
            'id': 'busqueda-repuesto'
        })
    )

class CarritoItemForm(forms.ModelForm):
    """Formulario para agregar/editar items en el carrito"""
    class Meta:
        model = CarritoItem
        fields = ['cantidad', 'precio_unitario']
        widgets = {
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'style': 'width: 80px;'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'style': 'width: 100px;'
            }),
        }

class VentaPOSForm(forms.ModelForm):
    """Formulario para completar la venta POS"""
    class Meta:
        model = VentaPOS
        fields = ['cliente', 'descuento', 'metodo_pago', 'observaciones']
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Cliente (opcional)'
            }),
            'descuento': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'value': '0'
            }),
            'metodo_pago': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones (opcional)'
            }),
        }

class ConfiguracionPOSForm(forms.ModelForm):
    """Formulario para configurar el sistema POS"""
    class Meta:
        model = ConfiguracionPOS
        fields = '__all__'
        widgets = {
            'nombre_empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control'}),
            'imprimir_ticket': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mostrar_descuentos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'permitir_venta_sin_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'margen_ganancia_default': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
        }

class ClienteRapidoForm(forms.ModelForm):
    """Formulario rápido para crear cliente desde POS"""
    class Meta:
        model = Cliente_Taller
        fields = ['rut', 'nombre', 'telefono']
        widgets = {
            'rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'RUT (12345678-9)',
                'required': True
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del cliente'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono (opcional)'
            }),
        }


class CotizacionForm(forms.ModelForm):
    """Formulario para crear cotizaciones"""
    class Meta:
        model = Cotizacion
        fields = ['cliente', 'descuento', 'observaciones', 'valida_hasta']
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Cliente (opcional)'
            }),
            'descuento': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'value': '0'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones (opcional)'
            }),
            'valida_hasta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }



