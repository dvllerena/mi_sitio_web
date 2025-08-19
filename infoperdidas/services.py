from django.db.models import Sum, Q
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from decimal import Decimal, getcontext
from perdidas.models import ConsumoEnergia
from facturacion.models import FacturacionMunicipio
from .models import ResultadoPerdidas
from datetime import datetime

getcontext().prec = 6

class CalculadorPerdidas:
    @staticmethod
    def get_datos_mes(codigo, mes, año):
        """Obtiene y valida los datos necesarios para el cálculo"""
        try:
            energia = ConsumoEnergia.objects.filter(
                municipio=codigo,
                fecha__year=año,
                fecha__month=mes
            ).aggregate(total=Sum('consumo'))['total'] or 0

            if energia <= 0:
                raise ValueError(f"Consumo energético inválido: {energia} MWh")

            facturacion = FacturacionMunicipio.objects.get(
                municipio=codigo,
                mes=mes,
                año=año
            )

            if facturacion.total_facturado is None or facturacion.total_facturado < 0:
                raise ValueError("Facturación inválida o negativa")

            return {
                'energia': float(energia),
                'fact_mayor': float(facturacion.facturacion_mayor),
                'fact_menor': float(facturacion.facturacion_menor),
                'total_ventas': float(facturacion.total_facturado)
            }

        except ObjectDoesNotExist:
            raise ValueError("Datos de facturación no encontrados")
        except Exception as e:
            raise ValueError(f"Error al obtener datos: {str(e)}")

    @classmethod
    @transaction.atomic
    def calcular_mes(cls, mes, año):
        """Calcula pérdidas para todos los municipios en un mes/año específico"""
        resultados = []
        errores = []

        for codigo, nombre in FacturacionMunicipio.MUNICIPIOS:
            try:
                datos = cls.get_datos_mes(codigo, mes, año)
                
                perdida_mwh = Decimal(datos['energia']) - Decimal(datos['total_ventas'])
                perdida_pct = (perdida_mwh / Decimal(datos['energia']) * 100) if datos['energia'] > 0 else 0

                resultado, created = ResultadoPerdidas.objects.update_or_create(
                    municipio=codigo,
                    mes=mes,
                    año=año,
                    defaults={
                        'energia_barra': float(datos['energia']),
                        'total_ventas': float(datos['total_ventas']),
                        'perdidas_mwh': float(round(perdida_mwh, 2)),
                        'perdidas_pct': float(round(perdida_pct, 2)),
                        'facturacion_mayor': float(datos['fact_mayor']),
                        'facturacion_menor': float(datos['fact_menor']),
                    }
                )

                resultados.append({
                    'municipio': nombre,
                    'codigo': codigo,
                    'resultado': resultado,
                    'fecha_calculo': resultado.actualizado_en if not created else resultado.creado_en
                })

            except ValueError as e:
                errores.append(f"{nombre}: {str(e)}")
                continue

        return resultados, errores

    @classmethod
    @transaction.atomic
    def calcular_acumulados(cls, año, mes_fin):
        """Calcula valores acumulados hasta el mes especificado por municipio"""
        for codigo, nombre in FacturacionMunicipio.MUNICIPIOS:
            try:
                consumos = ConsumoEnergia.objects.filter(
                    municipio=codigo,
                    fecha__year=año,
                    fecha__month__lte=mes_fin
                ).aggregate(total=Sum('consumo'))

                facturaciones = FacturacionMunicipio.objects.filter(
                    municipio=codigo,
                    año=año,
                    mes__lte=mes_fin
                ).aggregate(
                    total=Sum('total_facturado'),
                    mayor=Sum('facturacion_mayor'),
                    menor=Sum('facturacion_menor')
                )

                energia_acum = consumos['total'] or 0
                ventas_acum = facturaciones['total'] or 0
                perdidas_acum = Decimal(energia_acum) - Decimal(ventas_acum)
                acumulado_pct = (perdidas_acum / Decimal(energia_acum) * 100) if energia_acum > 0 else 0

                ResultadoPerdidas.objects.filter(
                    municipio=codigo,
                    año=año,
                    mes=mes_fin
                ).update(
                    acumulado_energia=round(float(energia_acum), 2),
                    acumulado_ventas=round(float(ventas_acum), 2),
                    acumulado_perdidas=round(float(perdidas_acum), 2),
                    acumulado_pct=round(float(acumulado_pct), 2),
                )

            except Exception as e:
                print(f"Error calculando acumulados para {nombre} ({codigo}): {str(e)}")
                continue
            
    @staticmethod
    def calcular_acumulado_provincial(año, mes):
        """Calcula el acumulado provincial incluyendo la estación cabecera"""
        energia_acum = ConsumoEnergia.objects.filter(
            fecha__year=año,
            fecha__month__lte=mes
        ).aggregate(total=Sum('consumo'))['total'] or 0

        ventas_acum_municipios = FacturacionMunicipio.objects.filter(
            año=año,
            mes__lte=mes
        ).aggregate(total=Sum('total_facturado'))['total'] or 0

        ventas_acum_cabecera = FacturacionMunicipio.objects.filter(
            municipio='CAR',
            año=año,
            mes__lte=mes
        ).aggregate(total=Sum('consumo_transmision'))['total'] or 0

        ventas_total = ventas_acum_municipios + ventas_acum_cabecera
        perdidas_total = energia_acum - ventas_total
        perdidas_pct = (perdidas_total / energia_acum * 100) if energia_acum > 0 else 0

        return {
            'acumulado_energia': round(energia_acum, 2),
            'acumulado_ventas': round(ventas_total, 2),
            'acumulado_perdidas': round(perdidas_total, 2),
            'acumulado_pct': round(perdidas_pct, 2)
        }
    
    
    @classmethod
    @transaction.atomic
    def guardar_datos_provincia(cls, datos_provincia, mes, año):
        """Guarda los datos calculados de la provincia en la base de datos"""
        try:
            resultado, created = ResultadoPerdidas.objects.update_or_create(
                municipio='PROVINCIA',
                mes=mes,
                año=año,
                defaults={
                    'energia_barra': round(float(datos_provincia['energia_barra']), 2),
                    'total_ventas': round(float(datos_provincia['total_ventas']), 2),
                    'perdidas_mwh': round(float(datos_provincia['perdidas_mwh']), 2),
                    'perdidas_pct': round(float(datos_provincia['perdidas_pct']), 2),
                    'facturacion_mayor': round(float(datos_provincia['fact_mayor']), 2),
                    'facturacion_menor': round(float(datos_provincia['fact_menor']), 2),
                    'acumulado_energia': round(float(datos_provincia['acumulado_energia']), 2),
                    'acumulado_ventas': round(float(datos_provincia['acumulado_ventas']), 2),
                    'acumulado_perdidas': round(float(datos_provincia['acumulado_perdidas']), 2),
                    'acumulado_pct': round(float(datos_provincia['acumulado_pct']), 2),
                    'plan_pct': round(float(datos_provincia.get('plan_pct', 0)), 2),
                    'plan_acum_pct': round(float(datos_provincia.get('plan_acum_pct', 0)), 2),
                }
            )
            return resultado
        except Exception as e:
            raise ValueError(f"Error guardando datos provinciales: {str(e)}")
