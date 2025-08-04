from django import forms
from django.core.exceptions import ValidationError
from .models import ConsumoEnergia
import pandas as pd
from datetime import date

MESES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
]

AÑOS = [(y, y) for y in range(2020, date.today().year + 1)]

class CargaConsumoForm(forms.Form):
    archivo_excel = forms.FileField(
        label='Archivo Excel (Columnas: municipio y consumo)',
        widget=forms.FileInput(attrs={'accept': '.xlsx, .xls'}))
    
    mes = forms.ChoiceField(
        label='Mes',
        choices=MESES,
        initial=date.today().month)
    
    año = forms.ChoiceField(
        label='Año',
        choices=AÑOS,
        initial=date.today().year)

    def clean_archivo_excel(self):
        archivo = self.cleaned_data.get('archivo_excel')
        if not archivo.name.endswith(('.xlsx', '.xls')):
            raise ValidationError("Solo se permiten archivos Excel (.xlsx, .xls)")
        return archivo

    def procesar_archivo(self):
        archivo = self.cleaned_data['archivo_excel']
        mes = int(self.cleaned_data['mes'])
        año = int(self.cleaned_data['año'])
        
        try:
            df = pd.read_excel(archivo)
            
            if not all(col in df.columns for col in ['municipio', 'consumo']):
                raise ValidationError("El archivo debe contener las columnas: municipio y consumo")
            
            municipios_obet = {
                'MAT': 'OBET Matanzas',
                'VAR': 'OBET Varadero',
                'CAR': 'OBET Cárdenas',
                'MAR': 'OBET Colón',
                'PER': 'OBET Jovellanos',
                'ARA': 'OBET Colón',
                'COL': 'OBET Colón',
                'JOV': 'OBET Jovellanos',
                'BET': 'OBET Jagüey',
                'UNI': 'OBET Unión',
                'LIM': 'OBET Unión',
                'CIE': 'OBET Jagüey',
                'JG': 'OBET Jagüey',
                'CAL': 'OBET Colón'
            }
            
            datos = []
            total_consumo = 0
            
            for _, row in df.iterrows():
                municipio_nombre = str(row['municipio']).strip().lower()
                municipio_codigo = next(
                    (code for code, name in ConsumoEnergia.MUNICIPIOS 
                     if name.lower() == municipio_nombre), None)
                
                if not municipio_codigo:
                    raise ValidationError(f"Municipio no reconocido: {row['municipio']}")
                
                try:
                    consumo = float(row['consumo'])
                    datos.append({
                        'obet': municipios_obet[municipio_codigo],
                        'municipio': municipio_codigo,
                        'consumo': consumo
                    })
                    total_consumo += consumo
                except ValueError:
                    raise ValidationError(f"Valor de consumo inválido para {row['municipio']}")
            
            return {
                'datos': datos,
                'total_consumo': total_consumo,
                'fecha': date(año, mes, 1)
            }
            
        except pd.errors.EmptyDataError:
            raise ValidationError("El archivo Excel está vacío")
        except Exception as e:
            raise ValidationError(f"Error al procesar el archivo: {str(e)}")

class EditarConsumoForm(forms.ModelForm):
    class Meta:
        model = ConsumoEnergia
        fields = ['consumo']
        widgets = {
            'consumo': forms.NumberInput(attrs={'step': '0.01'})
        }
    archivo_excel = forms.FileField(
        label='Archivo Excel (Columnas: municipio y consumo)',
        widget=forms.FileInput(attrs={'accept': '.xlsx, .xls'}))
    
    mes = forms.ChoiceField(
        label='Mes',
        choices=MESES,
        initial=date.today().month)
    
    año = forms.ChoiceField(
        label='Año',
        choices=AÑOS,
        initial=date.today().year)

    def clean_archivo_excel(self):
        archivo = self.cleaned_data.get('archivo_excel')
        if not archivo.name.endswith(('.xlsx', '.xls')):
            raise ValidationError("Solo se permiten archivos Excel (.xlsx, .xls)")
        return archivo

    def procesar_archivo(self):
        archivo = self.cleaned_data['archivo_excel']
        mes = int(self.cleaned_data['mes'])
        año = int(self.cleaned_data['año'])
        
        try:
            df = pd.read_excel(archivo)
            
            if not all(col in df.columns for col in ['municipio', 'consumo']):
                raise ValidationError("El archivo debe contener las columnas: municipio y consumo")
            
            # Obtenemos los municipios directamente del modelo
            municipios_disponibles = dict(ConsumoEnergia.MUNICIPIOS)
            municipios_map = {name.lower(): code for code, name in municipios_disponibles.items()}
            
            datos = []
            total_consumo = 0
            
            for _, row in df.iterrows():
                municipio_nombre = str(row['municipio']).strip().lower()
                municipio_codigo = municipios_map.get(municipio_nombre)
                
                if not municipio_codigo:
                    raise ValidationError(f"Municipio no reconocido: {row['municipio']}")
                
                try:
                    consumo = float(row['consumo'])
                    datos.append({
                        'municipio': municipios_disponibles[municipio_codigo],  # Nombre completo
                        'codigo_municipio': municipio_codigo,  # Código para guardar en BD
                        'consumo': consumo
                    })
                    total_consumo += consumo
                except ValueError:
                    raise ValidationError(f"Valor de consumo inválido para {row['municipio']}")
            
            return {
                'datos': datos,
                'total_consumo': total_consumo,
                'fecha': date(año, mes, 1)
            }
            
        except pd.errors.EmptyDataError:
            raise ValidationError("El archivo Excel está vacío")
        except Exception as e:
            raise ValidationError(f"Error al procesar el archivo: {str(e)}")