from django.db.models import Sum
from perdidas.models import ConsumoEnergia
from facturacion.models import FacturacionMunicipio

class CalculadorPerdidas:
    @staticmethod
    def get_datos_mes(codigo, nombre, mes, año):
        errores = []

        energia = ConsumoEnergia.objects.filter(
            municipio=codigo,
            fecha__year=año,
            fecha__month=mes
        ).aggregate(total=Sum('consumo'))['total'] or 0

        if energia == 0:
            errores.append("Consumo energético no encontrado")

        facturacion = FacturacionMunicipio.objects.filter(
            municipio=nombre,
            mes=mes,
            año=año
        ).first()

        if not facturacion:
            errores.append("Facturación no encontrada")

        if errores:
            raise ValueError(f"Datos incompletos para {nombre}-{mes}/{año}: {', '.join(errores)}")

        return {
            'energia': energia,
            'fact_mayor': facturacion.facturacion_mayor,
            'fact_menor': facturacion.facturacion_menor,
            'total_ventas': facturacion.total_facturado
        }

    @classmethod
    def calcular_mes(cls, mes, año):
        resultados = []
        errores = []

        for codigo, nombre in FacturacionMunicipio.MUNICIPIOS:
            try:
                datos = cls.get_datos_mes(codigo, nombre, mes, año)
                energia = datos['energia']
                fact_total = datos['total_ventas']
                perdida = round((energia - fact_total), 2)

                resultados.append({
                    'municipio': nombre,
                    'codigo': codigo,
                    'mes': mes,
                    'año': año,
                    'energia': energia,
                    'facturacion': fact_total,
                    'perdida': perdida,
                    'fact_mayor': datos['fact_mayor'],
                    'fact_menor': datos['fact_menor'],
                })
            except ValueError as e:
                errores.append(f"⛔ Error en municipio {codigo}: {str(e)}")

        return resultados, errores
