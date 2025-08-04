from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CargaFacturacionForm
from .models import FacturacionMunicipio
import pandas as pd
from django.contrib.auth.decorators import login_required

MAPA_MUNICIPIOS = {
    'Matanzas': 'MAT',
    'Varadero': 'VAR',
    'Cardenas': 'CAR',
    'Marti': 'MAR',
    'Perico': 'PER',
    'Arabos': 'ARA',
    'Colon': 'COL',
    'Jovellanos': 'JOV',
    'Betancourt': 'BET',
    'Union': 'UNI',
    'Union de Reyes': 'UNI',
    'Unión de Reyes': 'UNI',
    'Limonar': 'LIM',
    'Cienaga': 'CIE',
    'Cienaga de Zapata': 'CIE',
    'Ciénaga de Zapata': 'CIE',
    'Jaguey': 'JG',
    'Calimete': 'CAL'
}

@login_required
def facmayor_view(request):
    datos = None
    datos_guardados = None
    mes = None
    año = None
    
    if request.method == 'POST':
        form = CargaFacturacionForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data['archivo_excel']
            archivo_servicios = form.cleaned_data['archivo_servicios']
            mes = int(form.cleaned_data['mes'])
            año = int(form.cleaned_data['año'])
            
            try:
                # Procesar archivo principal
                xls = pd.ExcelFile(archivo)
                datos_tmp = []
                
                for nombre_hoja in xls.sheet_names:
                    df = xls.parse(nombre_hoja, header=None)
                    try:
                        fact_mayor = float(df.iloc[40, 2]) / 1000
                        fact_menor = float(df.iloc[37, 2]) / 1000
                        total = fact_mayor + fact_menor

                        codigo = MAPA_MUNICIPIOS.get(nombre_hoja.strip())
                        if not codigo:
                            messages.warning(request, f"No se reconoció el municipio '{nombre_hoja}'")
                            continue

                        datos_tmp.append({
                            'municipio': codigo,
                            'facturacion_mayor': fact_mayor,
                            'facturacion_menor': fact_menor,
                            'total_facturado': total,
                            'consumo_transmision': 0.0  # Inicializar
                        })
                    except Exception as e:
                        messages.warning(request, f"Error en hoja {nombre_hoja}: {e}")

                df_fact = pd.DataFrame(datos_tmp)
                df_serv = pd.read_excel(archivo_servicios)

                # 1. Consumo Transmisión (Nuevo requerimiento)
                consumo_transmision = df_serv.loc[df_serv['NTA'] == 'A1', 'KWHT'].sum() / 1000
                df_fact.loc[df_fact['municipio'] == 'MAT', 'facturacion_mayor'] -= consumo_transmision
                df_fact.loc[df_fact['municipio'] == 'MAT', 'consumo_transmision'] = consumo_transmision

                # 2. Ajustes existentes
                servicios_mat_uni = [124, 46]
                valor_mat_uni = df_serv.loc[df_serv['CODCLI'].isin(servicios_mat_uni), 'KWHT'].sum() / 1000
                df_fact.loc[df_fact['municipio'] == 'MAT', 'facturacion_mayor'] -= valor_mat_uni
                df_fact.loc[df_fact['municipio'] == 'UNI', 'facturacion_mayor'] += valor_mat_uni

                servicios_jag_col = [2623, 2633]
                valor_jag_col = df_serv.loc[df_serv['CODCLI'].isin(servicios_jag_col), 'KWHT'].sum() / 1000
                df_fact.loc[df_fact['municipio'] == 'JG', 'facturacion_mayor'] -= valor_jag_col
                df_fact.loc[df_fact['municipio'] == 'COL', 'facturacion_mayor'] += valor_jag_col

                servicios_jag_jov = [2449, 2443]
                valor_jag_jov = df_serv.loc[df_serv['CODCLI'].isin(servicios_jag_jov), 'KWHT'].sum() / 1000
                df_fact.loc[df_fact['municipio'] == 'JG', 'facturacion_mayor'] -= valor_jag_jov
                df_fact.loc[df_fact['municipio'] == 'JOV', 'facturacion_mayor'] += valor_jag_jov

                servicio_car = [665]
                valor_car = df_serv.loc[df_serv['CODCLI'].isin(servicio_car), 'KWHT'].sum() / 1000
                df_fact.loc[df_fact['municipio'] == 'CAR', 'facturacion_mayor'] -= valor_car
                df_fact.loc[df_fact['municipio'] == 'CAR', 'consumo_transmision'] = valor_car
                # Recalcular totales
                df_fact['facturacion_mayor'] = df_fact['facturacion_mayor'].round(2)
                df_fact['total_facturado'] = (df_fact['facturacion_mayor'] + df_fact['facturacion_menor']).round(2)

                datos = df_fact.to_dict('records')
                request.session['facturacion_datos'] = datos
                request.session['facturacion_mes'] = mes
                request.session['facturacion_año'] = año
                
            except Exception as e:
                messages.error(request, f"Error al procesar los archivos: {e}")
        else:
            messages.error(request, "Por favor corrija los errores en el formulario")
    else:
        form = CargaFacturacionForm(request.GET or None)
        if request.GET.get('mes') and request.GET.get('año'):
            mes = int(request.GET.get('mes'))
            año = int(request.GET.get('año'))

    datos_guardados = FacturacionMunicipio.objects.filter(mes=mes, año=año) if mes and año else None

    return render(request, 'facturacion/facmayor.html', {
        'form': form,
        'datos': datos,
        'mes': mes,
        'año': año,
        'mostrar_tabla': datos is not None,
        'datos_guardados': datos_guardados,
        'mostrar_guardados': datos_guardados is not None and datos_guardados.exists()
    })

@login_required
def guardar_facturacion(request):
    if request.method == 'POST' and 'facturacion_datos' in request.session:
        datos = request.session['facturacion_datos']
        mes = request.session['facturacion_mes']
        año = request.session['facturacion_año']
        try:
            for item in datos:
                FacturacionMunicipio.objects.update_or_create(
                    municipio=item['municipio'], mes=mes, año=año,
                    defaults={
                        'facturacion_mayor': item['facturacion_mayor'],
                        'facturacion_menor': item['facturacion_menor'],
                        'total_facturado': item['total_facturado'],
                        'consumo_transmision': item.get('consumo_transmision', 0.0)
                    }
                )
            messages.success(request, 'Facturación guardada exitosamente!')
            del request.session['facturacion_datos']
            del request.session['facturacion_mes']
            del request.session['facturacion_año']
        except Exception as e:
            messages.error(request, f'Error al guardar datos: {e}')
    return redirect('facturacion:facmayor')