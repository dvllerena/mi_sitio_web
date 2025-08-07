from django import forms

class PlanForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo Excel",
        help_text="Debe contener hojas 'Acumulados' y 'Mensuales'"
    )
    periodo = forms.CharField(
        label="Periodo",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Plan 2025'})
    )