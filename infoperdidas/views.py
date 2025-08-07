from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from calendar import month_name
from .models import ResultadoPerdidas
from facturacion.models import FacturacionMunicipio # Importación necesaria
from perdidas.models import ConsumoEnergia
from .services import CalculadorPerdidas
from datetime import datetime
from django.urls import reverse
import calendar

def _calcular_datos_provincia(municipios_data, año, mes, request):
    """
    Calcula los datos consolidados de la provincia:
    1. Suma de todos los municipios para el mes actual
    2. Acumulado hasta el mes actual, incluyendo estación cabecera
    """
    try:
        estacion_cabecera = FacturacionMunicipio.objects.get(
            municipio='CAR',
            mes=mes,
            año=año
        ).consumo_transmision or 0
    except ObjectDoesNotExist:
        estacion_cabecera = 0
        messages.warning(request, "No se encontraron datos de Estación Cabecera para Cárdenas")

    total_provincial = {
        'energia_barra': sum(m['energia_barra'] for m in municipios_data),
        'fact_mayor': sum(m['fact_mayor'] for m in municipios_data),
        'fact_menor': sum(m['fact_menor'] for m in municipios_data),
        'estacion_cabecera': estacion_cabecera,
        'nombre': 'PROVINCIA',
        'codigo': 'provincia',
        'plan_pct': 10.0,
        'plan_acum_pct': 10.0
    }

    total_provincial['total_ventas'] = (
        total_provincial['fact_mayor'] +
        total_provincial['fact_menor'] +
        total_provincial['estacion_cabecera']
    )
    total_provincial['perdidas_mwh'] = (
        total_provincial['energia_barra'] -
        total_provincial['total_ventas']
    )
    total_provincial['perdidas_pct'] = (
        (total_provincial['perdidas_mwh'] / total_provincial['energia_barra'] * 100)
        if total_provincial['energia_barra'] > 0 else 0
    )

    acumulado = CalculadorPerdidas.calcular_acumulado_provincial(año, mes)

    total_provincial['acumulado_energia'] = acumulado['acumulado_energia']
    total_provincial['acumulado_ventas'] = acumulado['acumulado_ventas']
    total_provincial['acumulado_perdidas'] = acumulado['acumulado_perdidas']
    total_provincial['acumulado_pct'] = acumulado['acumulado_pct']

    return total_provincial

def informe_perdidas(request):
    meses = [(i, calendar.month_name[i].capitalize()) for i in range(1, 13)]
    años = range(datetime.now().year, 2019, -1)
    
    try:
        if request.method == 'POST':
            mes = int(request.POST.get('mes'))
            año = int(request.POST.get('año'))
            if not (1 <= mes <= 12):
                raise ValueError("El mes debe estar entre 1 y 12.")
            
            resultados, errores = CalculadorPerdidas.calcular_mes(mes, año)
            
            for error in errores:
                messages.warning(request, error)
            if resultados:
                messages.success(request, f"Cálculos completados para {len(resultados)} municipios.")
            
            CalculadorPerdidas.calcular_acumulados(año, mes)
            
            return redirect(f"{reverse('infoperdidas:informe')}?mes={mes}&año={año}")

        mes = int(request.GET.get('mes', datetime.now().month))
        año = int(request.GET.get('año', datetime.now().year))
        
        if not (1 <= mes <= 12):
            raise ValueError("Mes inválido.")
        current_year = datetime.now().year
        if not (2020 <= año <= current_year + 1):
            raise ValueError("Año fuera de rango.")
            
        datos_municipios = []
        
        # 💡 Lógica corregida para obtener los municipios únicos del modelo FacturacionMunicipio
        municipios_unicos_data = FacturacionMunicipio.objects.values('municipio').distinct().order_by('municipio')
        municipios = [{'nombre': m['municipio'], 'codigo': m['municipio']} for m in municipios_unicos_data]
        
        for mun in municipios:
            try:
                resultado_mun = ResultadoPerdidas.objects.get(
                    municipio=mun['codigo'], mes=mes, año=año
                )
                datos_municipios.append({
                    'codigo': mun['codigo'],
                    'nombre': mun['nombre'],
                    'energia_barra': resultado_mun.energia_barra,
                    'total_ventas': resultado_mun.total_ventas,
                    'perdidas_mwh': resultado_mun.perdidas_mwh,
                    'perdidas_pct': resultado_mun.perdidas_pct,
                    'fact_mayor': resultado_mun.facturacion_mayor,
                    'fact_menor': resultado_mun.facturacion_menor,
                    'plan_pct': resultado_mun.plan_pct,
                    'acumulado_energia': resultado_mun.acumulado_energia,
                    'acumulado_perdidas': resultado_mun.acumulado_perdidas,
                    'acumulado_pct': resultado_mun.acumulado_pct,
                    'plan_acum_pct': resultado_mun.plan_acum_pct,
                })
            except ResultadoPerdidas.DoesNotExist:
                datos_municipios.append({
                    'codigo': mun['codigo'],
                    'nombre': mun['nombre'],
                    'energia_barra': 0, 'total_ventas': 0, 'perdidas_mwh': 0,
                    'perdidas_pct': 0, 'fact_mayor': 0, 'fact_menor': 0,
                    'plan_pct': 0, 'acumulado_energia': 0, 'acumulado_perdidas': 0,
                    'acumulado_pct': 0, 'plan_acum_pct': 0,
                })
        
        # Añade los datos consolidados de la provincia
        datos_provincia = _calcular_datos_provincia(datos_municipios, año, mes, request)
        datos_municipios.append(datos_provincia)

    except Exception as e:
        messages.error(request, f"Ocurrió un error inesperado: {str(e)}")
        mes = datetime.now().month
        año = datetime.now().year
        datos_municipios = []

    contexto = {
        'municipios': datos_municipios,
        'meses': meses,
        'mes_actual': mes,
        'años': años,
        'año_actual': año,
    }
    return render(request, 'infoperdidas/informe.html', contexto)

def calcular_acumulados(request, año):
    try:
        mes_actual = datetime.now().month
        CalculadorPerdidas.calcular_acumulados(año, mes_actual)
        messages.success(request, f"Acumulados calculados para el año {año}")
        return redirect('infoperdidas:informe')
    except Exception as e:
        messages.error(request, f"Error calculando acumulados: {str(e)}")
        return redirect('infoperdidas:informe')

def calcular_perdidas(request):
    if request.method == 'POST':
        try:
            mes = int(request.POST.get('mes'))
            año = int(request.POST.get('año'))
            if not (1 <= mes <= 12):
                raise ValueError("Mes debe estar entre 1 y 12")
            resultados, errores = CalculadorPerdidas.calcular_mes(mes, año)
            for error in errores:
                messages.warning(request, error)
            if resultados:
                messages.success(request, f"Cálculos completados para {len(resultados)} municipios")
            
            # 💡 Corrección aquí: Usamos 'redirect' con los parámetros de la URL
            return redirect(f'infoperdidas:informe?mes={mes}&año={año}')
            
        except ValueError as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('infoperdidas:calcular')
    
    # El código aquí abajo también tenía un error similar y una lógica extraña.
    # Te sugiero una estructura más simple si el método no es POST.
    # Si la vista solo debe manejar POST, puedes eliminar estas líneas.
    return redirect('infoperdidas:informe')
