from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from calendar import month_name
from .models import ResultadoPerdidas
from facturacion.models import FacturacionMunicipio
from perdidas.models import ConsumoEnergia
from .services import CalculadorPerdidas  # Importación correcta al inicio
from datetime import datetime
from django.urls import reverse
import calendar
from planes.models import Plan, DatosMunicipio, DatosUEB

# Mapeo de códigos de facturación a nombres completos en planes
MUNICIPIOS_MAP = {
    'MAT': 'Matanzas',
    'UNI': 'Unión de Reyes', 
    'LIM': 'Limonar',
    'COL': 'Colón',
    'CAL': 'Calimete',
    'ARA': 'Los Arabos',
    'MAR': 'Martí',
    'CAR': 'Cárdenas',
    'VAR': 'Varadero', 
    'JOV': 'Jovellanos',
    'PER': 'Perico',
    'JG': 'Jagüey Grande',
    'CIE': 'Ciénaga de Zapata',
    'BET': 'Pedro Betancourt',
    'PROVINCIA': 'PROVINCIA'
}

# Mapeo de meses en español
MESES_ESPANOL = {
    1: 'enero',
    2: 'febrero', 
    3: 'marzo',
    4: 'abril',
    5: 'mayo',
    6: 'junio',
    7: 'julio',
    8: 'agosto',
    9: 'septiembre',
    10: 'octubre',
    11: 'noviembre',
    12: 'diciembre'
}

def _get_nombre_plan(codigo_municipio):
    """Convierte el código de facturación al nombre completo usado en los planes"""
    return MUNICIPIOS_MAP.get(codigo_municipio.upper(), codigo_municipio)

def _obtener_valor_mes(datos_obj, mes):
    """Obtiene el valor del mes usando nombres de campos en español"""
    mes_espanol = MESES_ESPANOL[mes]
    return getattr(datos_obj, mes_espanol, 0)

def _calcular_datos_provincia(municipios_data, año, mes, request):
    """
    Calcula los datos consolidados de la provincia
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

    try:
        # Obtener plan del año
        plan_anual = Plan.objects.filter(periodo__contains=str(año)).first()
        
        if plan_anual:
            # Buscar datos provinciales MENSUALES (es_mensual=True)
            datos_provincia_mensual = DatosUEB.objects.filter(
                plan=plan_anual,
                nombre__icontains='PROVINCIA',
                es_mensual=True
            ).first()
            
            # Buscar datos provinciales ACUMULADOS (es_mensual=False)
            datos_provincia_acumulado = DatosUEB.objects.filter(
                plan=plan_anual,
                nombre__icontains='PROVINCIA',
                es_mensual=False
            ).first()
            
            # Obtener valor del mes actual para plan_pct (mensual) - CORREGIDO
            plan_pct = _obtener_valor_mes(datos_provincia_mensual, mes) if datos_provincia_mensual else 0
            
            # Obtener valor acumulado hasta el mes actual - CORREGIDO
            plan_acum_pct = _obtener_valor_mes(datos_provincia_acumulado, mes) if datos_provincia_acumulado else 0
        else:
            plan_pct = 0
            plan_acum_pct = 0
            messages.warning(request, "No se encontró plan provincial para el año seleccionado")
            
    except Exception as e:
        plan_pct = 0
        plan_acum_pct = 0
        messages.warning(request, f"Error al obtener plan provincial: {str(e)}")

    total_provincial = {
        'energia_barra': sum(m['energia_barra'] for m in municipios_data),
        'fact_mayor': sum(m['fact_mayor'] for m in municipios_data),
        'fact_menor': sum(m['fact_menor'] for m in municipios_data),
        'estacion_cabecera': estacion_cabecera,
        'nombre': 'PROVINCIA',
        'codigo': 'PROVINCIA',  # Cambiado de 'provincia' a 'PROVINCIA' para consistencia
        'plan_pct': plan_pct,
        'plan_acum_pct': plan_acum_pct
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

    # Usar el servicio importado correctamente
    acumulado = CalculadorPerdidas.calcular_acumulado_provincial(año, mes)

    total_provincial['acumulado_energia'] = acumulado['acumulado_energia']
    total_provincial['acumulado_ventas'] = acumulado['acumulado_ventas']
    total_provincial['acumulado_perdidas'] = acumulado['acumulado_perdidas']
    total_provincial['acumulado_pct'] = acumulado['acumulado_pct']

    return total_provincial


def informe_perdidas(request):
    # Cambiar meses a español para el template
    meses_espanol = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
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
        
        # Obtener municipios únicos
        municipios_unicos_data = FacturacionMunicipio.objects.values('municipio').distinct().order_by('municipio')
        municipios = [{'nombre': dict(FacturacionMunicipio.MUNICIPIOS).get(m['municipio'], m['municipio']), 
                      'codigo': m['municipio']} for m in municipios_unicos_data]
        
        # Obtener plan del año una sola vez
        plan_anual = Plan.objects.filter(periodo__contains=str(año)).first()
        
        for mun in municipios:
            try:
                # Obtener datos del plan para el municipio
                plan_pct = 0
                plan_acum_pct = 0
                
                if plan_anual:
                    try:
                        # Convertir nombre al formato de planes
                        nombre_plan = _get_nombre_plan(mun['codigo'])
                        
                        # Buscar datos MENSUALES del municipio
                        datos_mensuales = DatosMunicipio.objects.get(
                            nombre=nombre_plan,
                            plan=plan_anual,
                            es_mensual=True
                        )
                        
                        # Buscar datos ACUMULADOS del municipio
                        datos_acumulados = DatosMunicipio.objects.get(
                            nombre=nombre_plan,
                            plan=plan_anual,
                            es_mensual=False
                        )
                        
                        # Obtener valor del mes actual para plan_pct (mensual) - CORREGIDO
                        plan_pct = _obtener_valor_mes(datos_mensuales, mes)
                        
                        # Obtener valor acumulado hasta el mes actual - CORREGIDO
                        plan_acum_pct = _obtener_valor_mes(datos_acumulados, mes)
                        
                        # DIAGNÓSTICO: Verificar valores
                        print(f"{nombre_plan}: Mes {MESES_ESPANOL[mes]} = {plan_pct} (mensual), {plan_acum_pct} (acumulado)")
                        
                    except DatosMunicipio.DoesNotExist:
                        messages.warning(request, f"No se encontró plan para {mun['nombre']} (código: {mun['codigo']}, buscado como: {nombre_plan}) en {año}")
                    except Exception as e:
                        messages.warning(request, f"Error al obtener plan para {mun['nombre']}: {str(e)}")

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
                    'plan_pct': plan_pct,
                    'acumulado_energia': resultado_mun.acumulado_energia,
                    'acumulado_perdidas': resultado_mun.acumulado_perdidas,
                    'acumulado_pct': resultado_mun.acumulado_pct,
                    'plan_acum_pct': plan_acum_pct,
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
        
        # GUARDAR DATOS PROVINCIALES EN LA BASE DE DATOS
        try:
            CalculadorPerdidas.guardar_datos_provincia(datos_provincia, mes, año)
        except Exception as e:
            messages.warning(request, f"Error guardando datos provinciales: {str(e)}")
        
        datos_municipios.append(datos_provincia)

    except Exception as e:
        messages.error(request, f"Ocurrió un error inesperado: {str(e)}")
        mes = datetime.now().month
        año = datetime.now().year
        datos_municipios = []

    contexto = {
        'municipios': datos_municipios,
        'meses': meses_espanol,  # Usar meses en español
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
            
            return redirect(f'infoperdidas:informe?mes={mes}&año={año}')
            
        except ValueError as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('infoperdidas:calcular')
    
    return redirect('infoperdidas:informe')