from django.urls import path
from . import views

app_name = 'bonos'

urlpatterns = [
    path('configuracion/', views.configuracion_bonos, name='configuracion_bonos'),
    path('mecanicos/', views.lista_mecanicos_bonos, name='lista_mecanicos_bonos'),
]

