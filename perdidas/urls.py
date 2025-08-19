from django.urls import path
from . import views

app_name = 'perdidas'
urlpatterns = [
    path('calculo/', views.carga_consumo, name='calculo'),
    path('guardar-consumo/', views.guardar_consumo, name='guardar_consumo'),
    path('facmayor/', views.facmayor_view, name='facmayor'),
    path('infoperdidas/', views.infoperdidas_view, name='infoperdidas'),
    path('lventas/', views.lventas_view, name='lventas'),
]