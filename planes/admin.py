from django.contrib import admin
from .models import Plan, DatosMunicipio, DatosUEB

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('periodo', 'fecha_carga')
    list_filter = ('fecha_carga',)
    search_fields = ('periodo',)

@admin.register(DatosMunicipio)
class DatosMunicipioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'obet', 'plan', 'enero', 'febrero')
    list_filter = ('plan', 'obet', 'es_mensual')
    search_fields = ('nombre',)

@admin.register(DatosUEB)
class DatosUEBAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'plan', 'enero', 'febrero', 'es_mensual')
    list_filter = ('plan', 'es_mensual')
    search_fields = ('nombre',)