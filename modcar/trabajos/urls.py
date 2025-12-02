from django.urls import path
from . import views

app_name = 'trabajos'

urlpatterns = [
    path('', views.lista_trabajos, name='lista'),
    path('historial/', views.historial_trabajos, name='historial'),
    path('<int:pk>/', views.trabajo_detalle, name='detalle'),
    path('<int:pk>/pdf/', views.trabajo_pdf, name='pdf'),
    path('pizarra/', views.pizarra_view, name='pizarra'),
]

