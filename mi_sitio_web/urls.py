from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
    path('perdidas/', include('perdidas.urls')),
    path('facturacion/', include('facturacion.urls')),
    path('infoperdidas/', include('infoperdidas.urls')),
    path('planes/', include('planes.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)