from django import forms
from usuarios.models import Mecanico


class MecanicoForm(forms.ModelForm):
    class Meta:
        model = Mecanico
        fields = ['user', 'especialidad','activo']



