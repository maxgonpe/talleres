from django import forms
from configuracion.models import AdministracionTaller


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



