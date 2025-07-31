from django.contrib import admin
from .models import ConsumoEnergia

@admin.register(ConsumoEnergia)
class ConsumoEnergiaAdmin(admin.ModelAdmin):
    list_display = ('municipio', 'fecha', 'consumo', 'creado_en')
    list_filter = ('fecha', 'municipio')
    search_fields = ('municipio',)
    date_hierarchy = 'fecha'
    ordering = ('-fecha', 'municipio')