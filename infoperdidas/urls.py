from django.urls import path
from . import views
app_name= 'infoperdidas'
urlpatterns = [
    path('informe/', views.informe_perdidas, name='informe'),
]