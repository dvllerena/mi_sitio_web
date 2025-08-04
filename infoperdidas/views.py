from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.exceptions import ObjectDoesNotExist
from calendar import month_name
from .models import ResultadoPerdidas
from facturacion.models import FacturacionMunicipio
from perdidas.models import ConsumoEnergia
from .services import CalculadorPerdidas
from datetime import datetime

def _calcular_datos_provincia(municipios_data, año, mes,request):
    """
    Calcula los datos consolidados de la provincia basados en:
    1. Suma de todos los municipios para el mes actual
    2. Suma de pérdidas mensuales registradas para el acumulado
    """
    # Obtener consumo de transmisión de Cárdenas (Estación Cabecera) para el mes actual
    try:
        estacion_cabecera = FacturacionMunicipio.objects.get(
            municipio='CAR',
            mes=mes,
            año=año
        ).consumo_transmision or 0
    except ObjectDoesNotExist:
        estacion_cabecera = 0
        messages.warning(request, "No se encontraron datos de Estación Cabecera para Cárdenas")

    # 1. Calcular valores del MES ACTUAL para la provincia (suma de municipios)
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
    
    # Cálculos para el MES ACTUAL
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

    # 2. Calcular ACUMULADOS (sumando pérdidas mensuales registradas)
    resultados_acumulados = ResultadoPerdidas.objects.filter(
        año=año,
        mes__range=(1, mes)
    ).aggregate(
        suma_energia=Sum('energia_barra'),
        suma_perdidas=Sum('perdidas_mwh'),
        suma_ventas=Sum('total_ventas')
    )
    
    if resultados_acumulados['suma_energia']:
        total_provincial['acumulado_energia'] = round(resultados_acumulados['suma_energia'], 2)
        total_provincial['acumulado_ventas'] = round(resultados_acumulados['suma_ventas'], 2)
        total_provincial['acumulado_perdidas'] = round(total_provincial['acumulado_energia'] - total_provincial['acumulado_ventas'],2)
        
        # Calcular porcentaje acumulado
        if resultados_acumulados['suma_energia'] > 0:
            total_provincial['acumulado_pct'] = round(
                (resultados_acumulados['suma_perdidas'] / 
                 resultados_acumulados['suma_energia'] * 100), 
                2
            )
        else:
            total_provincial['acumulado_pct'] = 0
    else:
        # Si no hay datos acumulados (como en enero)
        total_provincial['acumulado_energia'] = total_provincial['energia_barra']
        total_provincial['acumulado_ventas'] = total_provincial['total_ventas']
        total_provincial['acumulado_perdidas'] = total_provincial['perdidas_mwh']
        total_provincial['acumulado_pct'] = total_provincial['perdidas_pct']
    
    return total_provincial

def informe_perdidas(request):
    try:
        mes = int(request.GET.get('mes', datetime.now().month))
        año = int(request.GET.get('año', datetime.now().year))
        
        if not (1 <= mes <= 12):
            raise ValueError("Mes inválido")
            
        current_year = datetime.now().year
        if not (2020 <= año <= current_year + 1):
            raise ValueError("Año fuera de rango")

    except ValueError as e:
        messages.error(request, f"Error en parámetros: {str(e)}")
        return redirect('infoperdidas:informe')

    # Obtener datos para todos los municipios
    municipios_data = []
    
    for codigo, nombre in FacturacionMunicipio.MUNICIPIOS:
        try:
            # Datos del mes actual
            consumo = ConsumoEnergia.objects.filter(
                municipio=codigo,
                fecha__year=año,
                fecha__month=mes
            ).aggregate(total=Sum('consumo'))['total'] or 0

            facturacion = FacturacionMunicipio.objects.filter(
                municipio=codigo,
                mes=mes,
                año=año
            ).first()

            # Datos acumulados
            consumos_acum = ConsumoEnergia.objects.filter(
                municipio=codigo,
                fecha__year=año,
                fecha__month__lte=mes
            ).aggregate(total=Sum('consumo'))['total'] or 0

            facturaciones_acum = FacturacionMunicipio.objects.filter(
                municipio=codigo,
                año=año,
                mes__lte=mes
            ).aggregate(
                total=Sum('total_facturado'),
                mayor=Sum('facturacion_mayor'),
                menor=Sum('facturacion_menor')
            )

            # Cálculos para municipios
            total_ventas = (facturacion.total_facturado if facturacion else 0)
            perdidas_mwh = consumo - total_ventas
            perdidas_pct = (perdidas_mwh / consumo * 100) if consumo > 0 else 0
            
            perdidas_acum = consumos_acum - (facturaciones_acum['total'] or 0)
            
            acumulado_pct = (perdidas_acum / consumos_acum * 100) if consumos_acum > 0 else 0

            # Datos del municipio
            municipio_data = {
                'codigo': codigo.lower(),
                'nombre': nombre,
                'energia_barra': consumo,
                'fact_mayor': facturacion.facturacion_mayor if facturacion else 0,
                'fact_menor': facturacion.facturacion_menor if facturacion else 0,
                'total_ventas': total_ventas,
                'perdidas_mwh': perdidas_mwh,
                'perdidas_pct': perdidas_pct,
                'acumulado_energia': round(consumos_acum, 2),
                'acumulado_ventas': round(facturaciones_acum['total'] or 0, 2),
                'acumulado_perdidas': round(perdidas_acum, 2),
                'acumulado_pct': round(acumulado_pct, 2),
                'plan_pct': 10.0,
                'plan_acum_pct': 10.0
            }

            municipios_data.append(municipio_data)

        except Exception as e:
            messages.error(request, f"Error procesando {nombre}: {str(e)}")
            continue
    
    # Calcular datos de la provincia
    total_provincial = _calcular_datos_provincia(municipios_data, año, mes,request)
    
    # Validación final de resultados
    if total_provincial['acumulado_perdidas'] < 0:
        messages.error(request, "Error: Pérdidas acumuladas negativas - verifique datos de entrada")
    
    # Agregar provincia al inicio
    municipios_data.insert(0, total_provincial)

    context = {
        'mes_actual': mes,
        'año_actual': año,
        'meses': [(i, f"{i:02d} - {month_name[i]}") for i in range(1, 13)],
        'años': range(2023, datetime.now().year + 2),
        'municipios': municipios_data,
    }

    return render(request, 'infoperdidas/informe.html', context)

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
            
            return redirect('infoperdidas:informe') + f'?mes={mes}&año={año}'
            
        except ValueError as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('infoperdidas:calcular')
    
    return render(request, 'infoperdidas/calcular.html')