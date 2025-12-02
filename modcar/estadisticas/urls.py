from django.urls import path
from . import views

app_name = 'estadisticas'

urlpatterns = [
    path('', views.estadisticas_trabajos, name='estadisticas_trabajos'),
]

