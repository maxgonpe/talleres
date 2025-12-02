from django import forms
from compras.models import Compra, CompraItem


class CompraForm(forms.ModelForm):
    """Formulario para crear/editar compras"""
    class Meta:
        model = Compra
        fields = ['proveedor', 'fecha_compra', 'observaciones']
        widgets = {
            'proveedor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del proveedor'
            }),
            'fecha_compra': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones sobre la compra (opcional)'
            }),
        }

class CompraItemForm(forms.ModelForm):
    """Formulario para agregar/editar items de compra"""
    class Meta:
        model = CompraItem
        fields = ['repuesto', 'cantidad', 'precio_unitario']
        widgets = {
            'repuesto': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccionar repuesto'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '1',
                'placeholder': 'Cantidad'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
        }



