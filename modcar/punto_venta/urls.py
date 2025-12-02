from django.urls import path
from . import views

app_name = 'punto_venta'

urlpatterns = [
    path('', views.pos_principal, name='pos_principal'),
]

