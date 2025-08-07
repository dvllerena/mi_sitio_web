from django.urls import path
from .views import PlanesView

app_name = 'planes'  # Esto define el namespace 'planes'

urlpatterns = [
    path('listar/', PlanesView.as_view(), name='listar'),  # Ahora la URL es planes/listar/
]