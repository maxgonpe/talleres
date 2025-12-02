"""
URL configuration for modtaller project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import panel_principal

urlpatterns = [
    path('', panel_principal, name='panel_principal'),
    path('admin/', admin.site.urls),
    # Incluir URLs de todas las apps
    path('diagnosticos/', include('diagnosticos.urls')),
    path('trabajos/', include('trabajos.urls')),
    path('inventario/', include('inventario.urls')),
    path('pos/', include('punto_venta.urls')),
    path('compras/', include('compras.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('bonos/', include('bonos.urls')),
    path('configuracion/', include('configuracion.urls')),
    path('estadisticas/', include('estadisticas.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

