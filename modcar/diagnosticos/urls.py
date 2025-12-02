from django.urls import path
from . import views

app_name = 'diagnosticos'

urlpatterns = [
    path('', views.lista_diagnosticos, name='lista'),
    path('ingreso/', views.ingreso_view, name='ingreso'),
    path('ingreso/exitoso/', views.ingreso_exitoso_view, name='ingreso_exitoso'),
    path('<int:pk>/editar/', views.editar_diagnostico, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_diagnostico, name='eliminar'),
    path('<int:pk>/aprobar/', views.aprobar_diagnostico, name='aprobar'),
    path('<int:pk>/exportar/', views.exportar_diagnostico_pdf, name='exportar_pdf'),
    path('exportar/excel/', views.exportar_diagnosticos_excel, name='exportar_excel'),
    path('exportar/pdf/', views.exportar_diagnosticos_pdf, name='exportar_pdf_lista'),
    path('acciones/<int:componente_id>/', views.acciones_por_componente, name='acciones_por_componente'),
    path('<int:diagnostico_id>/repuestos/', views.listar_repuestos_diagnostico, name='repuestos'),
    path('<int:diagnostico_id>/agregar-repuesto/', views.agregar_repuesto, name='agregar_repuesto'),
    path('sugerir-repuestos/', views.sugerir_repuestos, name='sugerir_repuestos'),
]

