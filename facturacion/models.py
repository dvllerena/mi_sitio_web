from django.db import models

class FacturacionMunicipio(models.Model):
    MUNICIPIOS = [
        ('MAT', 'Matanzas'),
        ('VAR', 'Varadero'),
        ('CAR', 'Cárdenas'),
        ('MAR', 'Martí'),
        ('PER', 'Perico'),
        ('ARA', 'Arabos'),
        ('COL', 'Colón'),
        ('JOV', 'Jovellanos'),
        ('BET', 'Betancourt'),
        ('UNI', 'Unión de Reyes'),
        ('LIM', 'Limonar'),
        ('CIE', 'Ciénaga de Zapata'),
        ('JAG', 'Jagüey Grande'),
        ('CAL', 'Calimete'),
    ]

    municipio = models.CharField(max_length=3, choices=MUNICIPIOS)
    mes = models.PositiveSmallIntegerField()
    año = models.PositiveSmallIntegerField()
    facturacion_mayor = models.FloatField()
    facturacion_menor = models.FloatField()
    total_facturado = models.FloatField()
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('municipio', 'mes', 'año')
        ordering = ['año', 'mes', 'municipio']

    def __str__(self):
        return f"{self.get_municipio_display()} - {self.mes}/{self.año}"
