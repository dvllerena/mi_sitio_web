from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from facturacion.models import FacturacionMunicipio


class ResultadoPerdidas(models.Model):
    MUNICIPIOS = FacturacionMunicipio.MUNICIPIOS
    
    municipio = models.CharField(
        max_length=3,
        choices=MUNICIPIOS,
        verbose_name="Municipio"
    )
    mes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    año = models.PositiveSmallIntegerField()
    energia_barra = models.FloatField(
        verbose_name="Energía en Barra (MWh)",
        validators=[MinValueValidator(0)]
    )
    total_ventas = models.FloatField(
        verbose_name="Total Facturado (MWh)",
        validators=[MinValueValidator(0)]
    )
    perdidas_mwh = models.FloatField(
        verbose_name="Pérdidas (MWh)",
        validators=[MinValueValidator(0)]
    )
    perdidas_pct = models.FloatField(
        verbose_name="Pérdidas (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    acumulado_energia = models.FloatField(default=0)
    acumulado_perdidas = models.FloatField(default=0)
    acumulado_pct = models.FloatField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)  # Nuevo campo
    facturacion_mayor = models.FloatField(default=0)
    facturacion_menor = models.FloatField(default=0)
    
    class Meta:
        db_table = 'infoperdidas_municipio'
        unique_together = [('municipio', 'mes', 'año')]
        verbose_name = "Resultado de Pérdidas"
        verbose_name_plural = "Resultados de Pérdidas"
        ordering = ['año', 'mes', 'municipio']
        indexes = [
            models.Index(fields=['municipio']),
            models.Index(fields=['mes']),
            models.Index(fields=['año']),
        ]

    def __str__(self):
        return f"{self.get_municipio_display()} - {self.mes:02d}/{self.año}"

    def save(self, *args, **kwargs):
        # Validaciones antes de guardar
        if self.energia_barra < 0 or self.total_ventas < 0:
            raise ValueError("Los valores de energía y ventas no pueden ser negativos")
            
        if self.total_ventas > self.energia_barra:
            raise ValueError("Las ventas no pueden ser mayores que la energía en barra")
            
        super().save(*args, **kwargs)