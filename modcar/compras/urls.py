from django.urls import path
from . import views

app_name = 'compras'

urlpatterns = [
    path('', views.compra_dashboard, name='compra_dashboard'),
    path('lista/', views.compra_list, name='compra_list'),
    path('nueva/', views.compra_create, name='compra_create'),
    path('<int:pk>/', views.compra_detail, name='compra_detail'),
]

