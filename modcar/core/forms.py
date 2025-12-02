from django import forms
from core.models import Componente, Cliente_Taller, Vehiculo, Accion, ComponenteAccion, VehiculoVersion
from core.models import normalizar_rut


class ClienteTallerForm(forms.ModelForm):
    """Formulario para el nuevo modelo Cliente_Taller con validación de RUT"""
    class Meta:
        model = Cliente_Taller
        fields = ['rut', 'nombre', 'telefono', 'email', 'direccion', 'activo']
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
        return normalizar_rut(rut)

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
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if rut:
            rut = rut.strip().upper()
            if not ClienteTallerForm()._validar_rut(rut):
                raise forms.ValidationError("RUT inválido. Formato: 12345678-9")
        return normalizar_rut(rut)
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


class ComponenteForm(forms.ModelForm):
    class Meta:
        model = Componente
        fields = ['nombre', 'activo', 'padre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
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



