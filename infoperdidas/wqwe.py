from django.shortcuts import render
from .models import ResultadoPerdidas
from facturacion.models import FacturacionMunicipio
from perdidas.models import ConsumoEnergia
from django.db.models import Sum
from calendar import month_name
from django.contrib import messages
from .services import CalculadorPerdidas

def informe_perdidas(request):
    mes = int(request.GET.get('mes', 1))
    año = int(request.GET.get('año', 2023))

    # Ejecutamos cálculos antes de mostrar
    CalculadorPerdidas.calcular_mes(mes, año)

    context = {
        'mes_actual': mes,
        'año_actual': año,
        'meses': [(i, f"{i} - {month_name[i]}") for i in range(1, 13)],
        'años': range(2020, 2031),
        'municipios': []
    }

    for codigo, nombre in FacturacionMunicipio.MUNICIPIOS:
        resultado = ResultadoPerdidas.objects.filter(
            municipio=codigo,
            mes=mes,
            año=año
        ).first()

        facturacion = FacturacionMunicipio.objects.filter(
            municipio=codigo,
            mes=mes,
            año=año
        ).first()

        consumos = ConsumoEnergia.objects.filter(
            municipio=codigo,
            fecha__year=año,
            fecha__month__lte=mes
        )

        facturaciones = FacturacionMunicipio.objects.filter(
            municipio=codigo,
            año=año,
            mes__lte=mes
        )

        energia_acum = consumos.aggregate(total=Sum('consumo'))['total'] or 0
        ventas_acum = facturaciones.aggregate(total=Sum('total_facturado'))['total'] or 0
        perdidas_acum = energia_acum - ventas_acum
        acumulado_pct = round((perdidas_acum / energia_acum * 100), 2) if energia_acum > 0 else 0

        # Diccionario uniforme, evita errores por claves faltantes
        municipio_data = {
            'codigo': codigo.lower(),
            'nombre': nombre,
            'energia_barra': resultado.energia_barra if resultado else 0,
            'fact_mayor': facturacion.facturacion_mayor if facturacion else 0,
            'fact_menor': facturacion.facturacion_menor if facturacion else 0,
            'total_ventas': facturacion.total_facturado if facturacion else 0,
            'perdidas_mwh': resultado.perdidas_mwh if resultado else 0,
            'perdidas_pct': resultado.perdidas_pct if resultado else 0,
            'acumulado_energia': energia_acum,
            'acumulado_ventas': ventas_acum,
            'acumulado_perdidas': perdidas_acum,
            'acumulado_pct': acumulado_pct,
            'plan_pct': 10.0,
            'plan_acum_pct': 10.0
        }

        # Si algún modelo está ausente, avisamos
        if not resultado or not facturacion:
            messages.warning(request, f"⚠️ Datos incompletos para {nombre} ({mes}/{año})")

        context['municipios'].append(municipio_data)

    return render(request, 'infoperdidas/informe.html', context)
