from django.urls import path
from .views import PlanesView, eliminar_plan

app_name = 'planes'

urlpatterns = [
    path('', PlanesView.as_view(), name='listar'),
    path('eliminar/<int:pk>/', eliminar_plan, name='eliminar_plan'),
]