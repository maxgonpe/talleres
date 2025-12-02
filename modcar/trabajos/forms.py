from django import forms
from trabajos.models import Trabajo, TrabajoFoto
from usuarios.models import Mecanico


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



