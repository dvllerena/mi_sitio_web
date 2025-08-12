from django import forms
from django.core.validators import FileExtensionValidator

class PlanForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo Excel",
        validators=[FileExtensionValidator(allowed_extensions=['xlsx'])],
        help_text="Formato requerido: Excel (.xlsx) con hojas 'Acumulados' y 'Mensuales'"
    )
    periodo = forms.CharField(
        label="Periodo",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: Plan 2025',
            'class': 'form-control'
        })
    )