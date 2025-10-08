from django import forms
from .models import Componente, Cliente, Vehiculo,\
                    Diagnostico,Accion, ComponenteAccion,\
                    Mecanico, Trabajo, TrabajoFoto,\
                    Venta, VentaItem, Repuesto, SesionVenta,\
                    CarritoItem, VentaPOS, VentaPOSItem, ConfiguracionPOS,\
                    Cotizacion, CotizacionItem, AdministracionTaller

class MecanicoForm(forms.ModelForm):
    class Meta:
        model = Mecanico
        fields = ['user', 'especialidad','activo']


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'telefono']

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['marca', 'modelo', 'anio', 'vin', 'placa', 'descripcion_motor']

#class DiagnosticoForm2(forms.ModelForm):
#    class Meta:
#        model = Diagnostico
#        fields = ['componente', 'descripcion_problema']
#

class DiagnosticoForm(forms.ModelForm):
    class Meta:
        model = Diagnostico
        fields = ['descripcion_problema']  # eliminamos 'vehiculo' porque se asigna en la vista
        widgets = {
            'componentes': forms.CheckboxSelectMultiple,  # o SelectMultiple si prefieres lista desplegable
        }


class ComponenteForm(forms.ModelForm):
    class Meta:
        model = Componente
        fields = ['nombre', 'activo', 'padre']  # <- sin descripcion
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            #'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'padre': forms.Select(attrs={'class': 'form-select'}),
        }

        def clean(self):
            cleaned = super().clean()
            nombre = (cleaned.get('nombre') or '').strip()
            padre  = cleaned.get('padre')
            qs = Componente.objects.filter(padre=padre, nombre__iexact=nombre)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                # Error “lindo” arriba del formulario
                raise forms.ValidationError("Ya existe un componente con ese nombre bajo el mismo padre.")
            return cleaned

class AccionForm(forms.ModelForm):
    class Meta:
        model = Accion
        fields = ["nombre"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Desarmar / Revisar / Calibrar ..."})
        }

    def clean_nombre(self):
        n = (self.cleaned_data.get("nombre") or "").strip()
        if not n:
            raise forms.ValidationError("El nombre es obligatorio.")
        # normaliza para evitar duplicados por mayúsculas/minúsculas
        if Accion.objects.exclude(pk=self.instance.pk).filter(nombre__iexact=n).exists():
            raise forms.ValidationError("Ya existe una acción con ese nombre.")
        return n


class ComponenteAccionForm(forms.ModelForm):
    componente = forms.ModelChoiceField(
        queryset=Componente.objects.all().order_by("nombre"),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    accion = forms.ModelChoiceField(
        queryset=Accion.objects.all().order_by("nombre"),
        widget=forms.Select(attrs={"class": "form-select"})
    )
    precio_mano_obra = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"})
    )

    class Meta:
        model = ComponenteAccion
        fields = ["componente", "accion", "precio_mano_obra"]

    def clean(self):
        cleaned = super().clean()
        comp = cleaned.get("componente")
        acc = cleaned.get("accion")
        if comp and acc:
            exists = ComponenteAccion.objects.exclude(pk=self.instance.pk).filter(
                componente=comp, accion=acc
            ).exists()
            if exists:
                raise forms.ValidationError("Ya existe un precio para ese Componente + Acción.")
        return cleaned

class AsignarMecanicosForm(forms.ModelForm):
    mecanicos = forms.ModelMultipleChoiceField(
        queryset=Mecanico.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Selecciona los mecánicos"
    )

    class Meta:
        model = Trabajo
        fields = ["mecanicos"]


class SubirFotoForm(forms.ModelForm):
    class Meta:
        model = TrabajoFoto
        fields = ["imagen", "descripcion"]



class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ["cliente", "metodo_pago"]

class VentaItemForm(forms.ModelForm):
    class Meta:
        model = VentaItem
        fields = ["repuesto_stock", "cantidad", "precio_unitario", "subtotal"]

class RepuestoForm(forms.ModelForm):
    class Meta:
        model = Repuesto
        fields = [
            "sku", "oem", "referencia", "nombre", "marca",
            "descripcion", "medida", "posicion", "unidad",
            "precio_costo", "precio_venta", "codigo_barra", "stock"
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

# ========================
# FORMULARIOS PARA POS
# ========================

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
        model = Cliente
        fields = ['nombre', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del cliente'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono (opcional)'
            }),
        }

# ========================
# FORMULARIOS PARA COTIZACIONES
# ========================

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


class AdministracionTallerForm(forms.ModelForm):
    class Meta:
        model = AdministracionTaller
        fields = [
            # Información básica
            'nombre_taller', 'direccion', 'telefono', 'email', 'rut',
            # Logos
            'logo_principal_png', 'logo_principal_svg', 'logo_secundario_png',
            # Fondo
            'imagen_fondo',
            # Políticas de seguridad
            'sesion_timeout_minutos', 'intentos_login_maximos', 'bloqueo_temporal_horas',
            'requiere_cambio_password', 'dias_validez_password',
            # Configuraciones
            'tema_por_defecto', 'mostrar_estadisticas_publicas', 
            'permitir_registro_usuarios', 'notificaciones_email'
        ]
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
            'sesion_timeout_minutos': forms.NumberInput(attrs={'min': 5, 'max': 480}),
            'intentos_login_maximos': forms.NumberInput(attrs={'min': 3, 'max': 10}),
            'bloqueo_temporal_horas': forms.NumberInput(attrs={'min': 1, 'max': 24}),
            'dias_validez_password': forms.NumberInput(attrs={'min': 0, 'max': 365}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos de archivos opcionales
        self.fields['logo_principal_png'].required = False
        self.fields['logo_principal_svg'].required = False
        self.fields['logo_secundario_png'].required = False
        self.fields['imagen_fondo'].required = False