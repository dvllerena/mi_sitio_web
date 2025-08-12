from django.db import models
from django.utils import timezone

class Plan(models.Model):
    periodo = models.CharField(max_length=100)
    archivo = models.FileField(upload_to='planes/')
    fecha_carga = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.periodo} - {self.fecha_carga.strftime('%d/%m/%Y')}"

class DatosMunicipio(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='municipios')
    nombre = models.CharField(max_length=100)
    obet = models.CharField(max_length=50, blank=True)
    es_mensual = models.BooleanField(default=False)
    
    # Campos mensuales
    enero = models.FloatField(null=True, blank=True)
    febrero = models.FloatField(null=True, blank=True)
    marzo = models.FloatField(null=True, blank=True)
    abril = models.FloatField(null=True, blank=True)
    mayo = models.FloatField(null=True, blank=True)
    junio = models.FloatField(null=True, blank=True)
    julio = models.FloatField(null=True, blank=True)
    agosto = models.FloatField(null=True, blank=True)
    septiembre = models.FloatField(null=True, blank=True)
    octubre = models.FloatField(null=True, blank=True)
    noviembre = models.FloatField(null=True, blank=True)
    diciembre = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.plan.periodo}"

class DatosUEB(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='uebs')
    nombre = models.CharField(max_length=100)
    es_mensual = models.BooleanField(default=False)
    
    # Campos mensuales
    enero = models.FloatField(null=True, blank=True)
    febrero = models.FloatField(null=True, blank=True)
    marzo = models.FloatField(null=True, blank=True)
    abril = models.FloatField(null=True, blank=True)
    mayo = models.FloatField(null=True, blank=True)
    junio = models.FloatField(null=True, blank=True)
    julio = models.FloatField(null=True, blank=True)
    agosto = models.FloatField(null=True, blank=True)
    septiembre = models.FloatField(null=True, blank=True)
    octubre = models.FloatField(null=True, blank=True)
    noviembre = models.FloatField(null=True, blank=True)
    diciembre = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.plan.periodo}"