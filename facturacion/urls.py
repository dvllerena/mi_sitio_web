from django.urls import path
from . import views

app_name = 'facturacion'
urlpatterns = [
    path('facmayor/', views.facmayor_view, name='facmayor'),
    path('guardar-facturacion/', views.guardar_facturacion, name='guardar_facturacion'),
]
