from django import forms
from inventario.models import Repuesto


class RepuestoForm(forms.ModelForm):
    class Meta:
        model = Repuesto
        fields = [
            "sku", "oem", "referencia", "nombre", "marca",
            "descripcion", "medida", "posicion", "unidad",
            "precio_costo", "precio_venta", "codigo_barra",
            "stock", "origen_repuesto", "cod_prov", "marca_veh", "tipo_de_motor", "carroceria"
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "tipo_de_motor": forms.Textarea(attrs={"rows": 2, "placeholder": "Ej: 1.6L, 2.0L Turbo, V6, etc.", "class": "form-control"}),
            "origen_repuesto": forms.TextInput(attrs={"placeholder": "Ej: Original, Alternativo, Reconstruido", "class": "form-control"}),
            "cod_prov": forms.TextInput(attrs={"placeholder": "Código del proveedor", "class": "form-control"}),
            "marca_veh": forms.TextInput(attrs={"placeholder": "Ej: Toyota, Honda, Ford", "class": "form-control"}),
            "carroceria": forms.TextInput(attrs={"placeholder": "Ej: Sedán, Hatchback, SUV, Pickup", "class": "form-control"}),
        }



