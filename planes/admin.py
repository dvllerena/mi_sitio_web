from django.contrib import admin
from .models import Plan, DatosMunicipio, DatosUEB

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('periodo', 'fecha_carga')
    search_fields = ('periodo',)

@admin.register(DatosMunicipio)
class DatosMunicipioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'plan', 'enero', 'febrero')  # Añade más meses si necesitas
    list_filter = ('plan',)
    search_fields = ('nombre',)

@admin.register(DatosUEB)
class DatosUEBAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'plan', 'enero', 'febrero')  # Añade más meses si necesitas
    list_filter = ('plan',)
    search_fields = ('nombre',)