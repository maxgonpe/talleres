from django.contrib import admin
from car.views_identidad import identidad_visual
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from car.views import panel_principal, get_vehiculos_por_cliente
from car.views_estilos import estilos

urlpatterns = [
    path('', panel_principal, name='panel_principal'),
    path('admin/', admin.site.urls),
    path('estilos/identidad/', identidad_visual, name='identidad_visual'),
    path('estilos/', estilos, name='estilos'),
    # IMPORTANTE: Esta ruta debe estar ANTES de incluir car.urls para que tenga prioridad
    path('api/vehiculos/<str:cliente_id>/', get_vehiculos_por_cliente, name='api_vehiculos_por_cliente'),
    path('car/', include('car.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
