from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.RepuestoListView.as_view(), name='lista'),
    path('crear/', views.RepuestoCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.RepuestoUpdateView.as_view(), name='editar'),
    path('<int:pk>/eliminar/', views.RepuestoDeleteView.as_view(), name='eliminar'),
    path('<int:pk>/compatibilidad/', views.repuesto_compatibilidad, name='compatibilidad'),
    path('lookup/', views.repuesto_lookup, name='lookup'),
    path('buscar-insumos/', views.buscar_insumos, name='buscar_insumos'),
    path('compatibilidad-api/<int:repuesto_id>/', views.repuesto_compatibilidad_api, name='compatibilidad_api'),
    path('repuestos-externos/', views.buscar_repuestos_externos_json, name='repuestos_externos'),
    path('agregar-externo/', views.agregar_repuesto_externo, name='agregar_externo'),
    path('agregar-externo-rapido/', views.agregar_repuesto_externo_rapido, name='agregar_externo_rapido'),
]

