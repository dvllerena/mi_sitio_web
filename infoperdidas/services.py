from django.db.models import Sum, Q
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from decimal import Decimal, getcontext
from perdidas.models import ConsumoEnergia
from facturacion.models import FacturacionMunicipio
from .models import ResultadoPerdidas

getcontext().prec = 6

class CalculadorPerdidas:
    @staticmethod
    def get_datos_mes(codigo, mes, año):
        """Obtiene y valida los datos necesarios para el cálculo"""
        try:
            # Consulta optimizada para energía
            energia = ConsumoEnergia.objects.filter(
                municipio=codigo,
                fecha__year=año,
                fecha__month=mes
            ).aggregate(total=Sum('consumo'))['total'] or 0

            if energia <= 0:
                raise ValueError(f"Consumo energético inválido: {energia} MWh")

            # Obtener facturación
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
                
                # Calcular pérdidas con precisión decimal
                perdida_mwh = Decimal(datos['energia']) - Decimal(datos['total_ventas'])
                perdida_pct = (perdida_mwh / Decimal(datos['energia']) * 100) if datos['energia'] > 0 else 0

                # Crear/actualizar registro
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
                    'resultado': resultado
                })

            except ValueError as e:
                errores.append(f"{nombre}: {str(e)}")
                continue

        return resultados, errores

    @classmethod
    @transaction.atomic
    def calcular_acumulados(cls, año, mes_fin):
        """Calcula valores acumulados hasta el mes especificado"""
        for codigo, nombre in FacturacionMunicipio.MUNICIPIOS:
            try:
                # Consultas optimizadas para acumulados
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

                # Actualizar solo el registro del mes final
                ResultadoPerdidas.objects.filter(
                    municipio=codigo,
                    año=año,
                    mes=mes_fin
                ).update(
                    acumulado_energia=round(float(energia_acum), 2),
                    acumulado_ventas=round(float(ventas_acum), 2),
                    acumulado_perdidas=round(float(perdidas_acum), 2),
                    acumulado_pct=round(float(acumulado_pct), 2),
                    acumulado_fact_mayor=round(float(facturaciones['mayor'] or 0), 2),
                    acumulado_fact_menor=round(float(facturaciones['menor'] or 0), 2)
                )

            except Exception as e:
                print(f"Error calculando acumulados para {nombre} ({codigo}): {str(e)}")
                continue