from django.db import models
from django.core.validators import MinValueValidator

class ConsumoEnergia(models.Model):
    OBET_CHOICES = [
        ('OBET Colón', 'OBET Colón (Calimete, Los Arabos, Martí, Colón)'),
        ('OBET Jagüey', 'OBET Jagüey (Jagüey Grande, Pedro Betancourt, Ciénaga de Zapata)'),
        ('OBET Unión', 'OBET Unión de Reyes (Unión de Reyes, Limonar)'),
        ('OBET Matanzas', 'OBET Matanzas (Matanzas)'),
        ('OBET Jovellanos', 'OBET Jovellanos (Jovellanos, Perico)'),
        ('OBET Cárdenas', 'OBET Cárdenas (Cárdenas)'),
        ('OBET Varadero', 'OBET Varadero (Varadero)'),
    ]
    
    MUNICIPIOS = [
        ('MAT', 'Matanzas'),
        ('VAR', 'Varadero'),
        ('CAR', 'Cárdenas'),
        ('MAR', 'Martí'),
        ('PER', 'Perico'),
        ('ARA', 'Los Arabos'),
        ('COL', 'Colón'),
        ('JOV', 'Jovellanos'),
        ('BET', 'Pedro Betancourt'),
        ('UNI', 'Unión de Reyes'),
        ('LIM', 'Limonar'),
        ('CIE', 'Ciénaga de Zapata'),
        ('JG', 'Jagüey Grande'),
        ('CAL', 'Calimete'),
    ]

    obet = models.CharField(max_length=20, choices=OBET_CHOICES)
    municipio = models.CharField(max_length=3, choices=MUNICIPIOS)
    fecha = models.DateField()
    consumo = models.FloatField(validators=[MinValueValidator(0)])
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perdidas_consumoenergia'
        verbose_name = "Consumo de Energía"
        verbose_name_plural = "Consumos de Energía"
        unique_together = ('municipio', 'fecha')
        ordering = ['fecha', 'obet']
        
    def __str__(self):
        return f"{self.get_municipio_display()} ({self.get_obet_display()}) - {self.fecha.strftime('%B %Y')}"
    
