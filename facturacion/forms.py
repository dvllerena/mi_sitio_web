from django import forms

class CargaFacturacionForm(forms.Form):
    archivo_excel = forms.FileField(
        label='Archivo Excel de Facturación',
        widget=forms.FileInput(attrs={'accept': '.xlsx, .xls'})
    )
    mes = forms.ChoiceField(label='Mes', choices=[(i, i) for i in range(1, 13)])
    año = forms.ChoiceField(label='Año', choices=[(y, y) for y in range(2020, 2051)])
    archivo_servicios = forms.FileField(label="Archivo Servicios")
