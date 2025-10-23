from django import forms
from .models import Componente, Cliente, Cliente_Taller, Vehiculo,\
                    Diagnostico,Accion, ComponenteAccion,\
                    Mecanico, Trabajo, TrabajoFoto,\
                    Venta, VentaItem, Repuesto, SesionVenta,\
                    CarritoItem, VentaPOS, VentaPOSItem, ConfiguracionPOS,\
                    Cotizacion, CotizacionItem, AdministracionTaller,\
                    Compra, CompraItem, VehiculoVersion

class MecanicoForm(forms.ModelForm):
    class Meta:
        model = Mecanico
        fields = ['user', 'especialidad','activo']


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'telefono']


class ClienteTallerForm(forms.ModelForm):
    """Formulario para el nuevo modelo Cliente_Taller con validación de RUT"""
    class Meta:
        model = Cliente_Taller
        fields = ['rut', 'nombre', 'telefono', 'email', 'direccion']
        widgets = {
            'rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 12345678-9',
                'pattern': '[0-9]{7,8}-[0-9Kk]',
                'title': 'Formato: 12345678-9'
            }),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if rut:
            # Validación básica de RUT chileno
            rut = rut.strip().upper()
            if not self._validar_rut(rut):
                raise forms.ValidationError("RUT inválido. Formato: 12345678-9")
        return rut

    def _validar_rut(self, rut):
        """Valida RUT chileno"""
        try:
            rut = rut.replace('-', '')
            if len(rut) < 8:
                return False
            
            cuerpo = rut[:-1]
            dv = rut[-1]
            
            # Validar que el cuerpo sean solo números
            if not cuerpo.isdigit():
                return False
            
            # Calcular dígito verificador
            suma = 0
            multiplicador = 2
            
            for i in reversed(cuerpo):
                suma += int(i) * multiplicador
                multiplicador = multiplicador + 1 if multiplicador < 7 else 2
            
            resto = suma % 11
            dv_calculado = 11 - resto
            
            if dv_calculado == 11:
                dv_calculado = '0'
            elif dv_calculado == 10:
                dv_calculado = 'K'
            else:
                dv_calculado = str(dv_calculado)
            
            return dv == dv_calculado
        except:
            return False


class ClienteTallerRapidoForm(forms.ModelForm):
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
                'placeholder': 'Nombre del cliente',
                'required': True
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono (opcional)'
            }),
        }

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


# ========================
# FORMULARIOS PARA COMPRAS
# ========================

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


# ========================
# FORMULARIOS PARA VEHÍCULOS
# ========================

class VehiculoVersionForm(forms.ModelForm):
    """Formulario para crear/editar versiones de vehículos"""
    class Meta:
        model = VehiculoVersion
        fields = ['marca', 'modelo', 'anio_desde', 'anio_hasta', 'motor', 'carroceria']
        widgets = {
            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Toyota, Honda, Ford'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Corolla, Civic, Focus'
            }),
            'anio_desde': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1900',
                'max': '2030',
                'placeholder': '2020'
            }),
            'anio_hasta': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1900',
                'max': '2030',
                'placeholder': '2024'
            }),
            'motor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1.6L, 2.0L Turbo, V6'
            }),
            'carroceria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Sedán, Hatchback, SUV'
            }),
        }