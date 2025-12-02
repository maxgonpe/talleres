from django import forms
from diagnosticos.models import Diagnostico


class DiagnosticoForm(forms.ModelForm):
    class Meta:
        model = Diagnostico
        fields = ['descripcion_problema']
        widgets = {
            'componentes': forms.CheckboxSelectMultiple,
        }



