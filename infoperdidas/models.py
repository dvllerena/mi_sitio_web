from django.db import models
from facturacion.models import FacturacionMunicipio


class ResultadoPerdidas(models.Model):
    MUNICIPIOS = FacturacionMunicipio.MUNICIPIOS  # Usamos los mismos choices
    
    municipio = models.CharField(
        max_length=3,
        choices=MUNICIPIOS,
        verbose_name="Municipio"
    )
    mes = models.PositiveSmallIntegerField()
    año = models.PositiveSmallIntegerField()
    energia_barra = models.FloatField(verbose_name="Energía en Barra (MWh)")
    total_ventas = models.FloatField(verbose_name="Total Facturado (MWh)")
    perdidas_mwh = models.FloatField(verbose_name="Pérdidas (MWh)")
    perdidas_pct = models.FloatField(verbose_name="Pérdidas (%)")
    acumulado_energia = models.FloatField(default=0)
    acumulado_perdidas = models.FloatField(default=0)
    acumulado_pct = models.FloatField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    facturacion_mayor = models.FloatField(default=0)
    facturacion_menor = models.FloatField(default=0)
    
    class Meta:
        unique_together = [('municipio', 'mes', 'año')]  # Nota: usamos lista en lugar de tupla
        verbose_name = "Resultado de Pérdidas"
        verbose_name_plural = "Resultados de Pérdidas"

    def __str__(self):
        return f"{self.get_municipio_display()} - {self.mes}/{self.año}"