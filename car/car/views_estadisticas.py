from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from datetime import timedelta, datetime
from decimal import Decimal

from .models import Trabajo, Diagnostico, AdministracionTaller
from .decorators import requiere_permiso


@login_required
@requiere_permiso('trabajos')
def estadisticas_trabajos(request):
    """
    Vista de estadísticas de trabajos
    Analiza tiempos, eficiencia, utilidad y avances
    """
    
    # Obtener configuración del taller
    config = AdministracionTaller.get_configuracion_activa()
    
    # Fechas para cálculos
    ahora = timezone.now()
    inicio_semana = ahora - timedelta(days=7)
    inicio_mes = ahora - timedelta(days=30)
    
    # ========================
    # 1. ESTADÍSTICAS GENERALES
    # ========================
    total_trabajos = Trabajo.objects.count()
    trabajos_activos = Trabajo.objects.exclude(estado='entregado').count()
    trabajos_completados = Trabajo.objects.filter(estado='completado').count()
    trabajos_entregados = Trabajo.objects.filter(estado='entregado').count()
    
    # Trabajos por estado con porcentajes
    trabajos_por_estado_raw = Trabajo.objects.values('estado').annotate(
        cantidad=Count('id')
    ).order_by('estado')
    
    trabajos_por_estado = []
    for estado_data in trabajos_por_estado_raw:
        porcentaje = (estado_data['cantidad'] / total_trabajos * 100) if total_trabajos > 0 else 0
        trabajos_por_estado.append({
            'estado': estado_data['estado'],
            'cantidad': estado_data['cantidad'],
            'porcentaje': round(porcentaje, 1)
        })
    
    # ========================
    # 2. TIEMPOS DE RESPUESTA
    # ========================
    # Tiempo desde diagnóstico hasta aprobación (en horas)
    diagnosticos_aprobados = Diagnostico.objects.filter(
        estado='aprobado',
        fecha_aceptacion__isnull=False
    )
    
    tiempos_respuesta = []
    for diag in diagnosticos_aprobados:
        if diag.fecha and diag.fecha_aceptacion:
            delta = diag.fecha_aceptacion - diag.fecha
            tiempos_respuesta.append(delta.total_seconds() / 3600)  # En horas
    
    tiempo_respuesta_promedio = sum(tiempos_respuesta) / len(tiempos_respuesta) if tiempos_respuesta else 0
    
    # ========================
    # 3. TIEMPO EN CADA ETAPA
    # ========================
    trabajos_con_fechas = Trabajo.objects.filter(
        fecha_inicio__isnull=False
    )
    
    tiempos_etapas = {
        'iniciado': [],
        'trabajando': [],
        'completado': [],
        'entregado': []
    }
    
    # Calcular días promedio en cada etapa
    for estado in ['iniciado', 'trabajando', 'completado', 'entregado']:
        trabajos_estado = trabajos_con_fechas.filter(estado=estado)
        for trabajo in trabajos_estado:
            if trabajo.fecha_inicio:
                fecha_fin = trabajo.fecha_fin if trabajo.fecha_fin else ahora
                delta = fecha_fin - trabajo.fecha_inicio
                tiempos_etapas[estado].append(delta.days)
    
    dias_promedio_por_etapa = {
        estado: sum(tiempos) / len(tiempos) if tiempos else 0
        for estado, tiempos in tiempos_etapas.items()
    }
    
    # Días promedio en el taller (todos los trabajos)
    # Calcular manualmente porque dias_en_taller es una propiedad, no un campo
    dias_totales = []
    for trabajo in trabajos_con_fechas:
        dias_totales.append(trabajo.dias_en_taller)
    dias_promedio_taller = sum(dias_totales) / len(dias_totales) if dias_totales else 0
    
    # ========================
    # 4. VEHÍCULOS INGRESADOS
    # ========================
    vehiculos_semana = Trabajo.objects.filter(
        fecha_inicio__gte=inicio_semana
    ).count()
    
    vehiculos_mes = Trabajo.objects.filter(
        fecha_inicio__gte=inicio_mes
    ).count()
    
    # Promedio semanal (últimas 4 semanas)
    semanas_anteriores = []
    for i in range(4):
        inicio_sem = inicio_semana - timedelta(weeks=i+1)
        fin_sem = inicio_semana - timedelta(weeks=i)
        vehiculos_sem = Trabajo.objects.filter(
            fecha_inicio__gte=inicio_sem,
            fecha_inicio__lt=fin_sem
        ).count()
        semanas_anteriores.append(vehiculos_sem)
    
    promedio_semanal = sum(semanas_anteriores) / len(semanas_anteriores) if semanas_anteriores else 0
    
    # ========================
    # 5. UTILIDAD Y FINANCIERO
    # ========================
    # Total de mano de obra (todos los trabajos)
    total_mano_obra = Decimal('0')
    total_repuestos = Decimal('0')
    total_ingresos = Decimal('0')
    
    trabajos_con_totales = Trabajo.objects.all()
    for trabajo in trabajos_con_totales:
        total_mano_obra += trabajo.total_mano_obra or Decimal('0')
        total_repuestos += trabajo.total_repuestos or Decimal('0')
    
    total_ingresos = total_mano_obra + total_repuestos
    
    # Promedio por trabajo
    promedio_mano_obra = total_mano_obra / total_trabajos if total_trabajos > 0 else Decimal('0')
    promedio_repuestos = total_repuestos / total_trabajos if total_trabajos > 0 else Decimal('0')
    promedio_ingresos = total_ingresos / total_trabajos if total_trabajos > 0 else Decimal('0')
    
    # Trabajos completados esta semana
    trabajos_completados_semana = Trabajo.objects.filter(
        estado__in=['completado', 'entregado'],
        fecha_fin__gte=inicio_semana
    ).count()
    
    # Ingresos de la semana
    ingresos_semana_mano_obra = Decimal('0')
    ingresos_semana_repuestos = Decimal('0')
    trabajos_semana = Trabajo.objects.filter(fecha_inicio__gte=inicio_semana)
    for trabajo in trabajos_semana:
        ingresos_semana_mano_obra += trabajo.total_mano_obra or Decimal('0')
        ingresos_semana_repuestos += trabajo.total_repuestos or Decimal('0')
    ingresos_semana = ingresos_semana_mano_obra + ingresos_semana_repuestos
    
    # ========================
    # 6. PORCENTAJE DE AVANCE
    # ========================
    porcentajes_avance = []
    for trabajo in Trabajo.objects.all():
        porcentajes_avance.append(trabajo.porcentaje_avance)
    
    promedio_avance = sum(porcentajes_avance) / len(porcentajes_avance) if porcentajes_avance else 0
    
    # Trabajos por rango de avance con porcentajes
    avance_0_25 = sum(1 for p in porcentajes_avance if 0 <= p < 25)
    avance_25_50 = sum(1 for p in porcentajes_avance if 25 <= p < 50)
    avance_50_75 = sum(1 for p in porcentajes_avance if 50 <= p < 75)
    avance_75_100 = sum(1 for p in porcentajes_avance if 75 <= p <= 100)
    
    # Calcular porcentajes de distribución
    porcentaje_avance_0_25 = (avance_0_25 / total_trabajos * 100) if total_trabajos > 0 else 0
    porcentaje_avance_25_50 = (avance_25_50 / total_trabajos * 100) if total_trabajos > 0 else 0
    porcentaje_avance_50_75 = (avance_50_75 / total_trabajos * 100) if total_trabajos > 0 else 0
    porcentaje_avance_75_100 = (avance_75_100 / total_trabajos * 100) if total_trabajos > 0 else 0
    
    # ========================
    # 7. EFICIENCIA Y PRODUCTIVIDAD
    # ========================
    # Tasa de completación (trabajos completados / total)
    tasa_completacion = (trabajos_completados / total_trabajos * 100) if total_trabajos > 0 else 0
    
    # Tasa de entrega (trabajos entregados / total)
    tasa_entrega = (trabajos_entregados / total_trabajos * 100) if total_trabajos > 0 else 0
    
    # Trabajos completados esta semana vs promedio
    completados_vs_promedio = trabajos_completados_semana - (promedio_semanal * 0.7)  # Asumiendo 70% se completan
    
    context = {
        'config': config,
        
        # Generales
        'total_trabajos': total_trabajos,
        'trabajos_activos': trabajos_activos,
        'trabajos_completados': trabajos_completados,
        'trabajos_entregados': trabajos_entregados,
        'trabajos_por_estado': trabajos_por_estado,
        
        # Tiempos
        'tiempo_respuesta_promedio': round(tiempo_respuesta_promedio, 2),
        'dias_promedio_por_etapa': dias_promedio_por_etapa,
        'dias_promedio_taller': round(dias_promedio_taller, 1),
        
        # Vehículos
        'vehiculos_semana': vehiculos_semana,
        'vehiculos_mes': vehiculos_mes,
        'promedio_semanal': round(promedio_semanal, 1),
        
        # Financiero
        'total_mano_obra': total_mano_obra,
        'total_repuestos': total_repuestos,
        'total_ingresos': total_ingresos,
        'promedio_mano_obra': promedio_mano_obra,
        'promedio_repuestos': promedio_repuestos,
        'promedio_ingresos': promedio_ingresos,
        'trabajos_completados_semana': trabajos_completados_semana,
        'ingresos_semana': ingresos_semana,
        'ingresos_semana_mano_obra': ingresos_semana_mano_obra,
        'ingresos_semana_repuestos': ingresos_semana_repuestos,
        
        # Avance
        'promedio_avance': round(promedio_avance, 1),
        'avance_0_25': avance_0_25,
        'avance_25_50': avance_25_50,
        'avance_50_75': avance_50_75,
        'avance_75_100': avance_75_100,
        'porcentaje_avance_0_25': round(porcentaje_avance_0_25, 1),
        'porcentaje_avance_25_50': round(porcentaje_avance_25_50, 1),
        'porcentaje_avance_50_75': round(porcentaje_avance_50_75, 1),
        'porcentaje_avance_75_100': round(porcentaje_avance_75_100, 1),
        
        # Eficiencia
        'tasa_completacion': round(tasa_completacion, 1),
        'tasa_entrega': round(tasa_entrega, 1),
        'completados_vs_promedio': round(completados_vs_promedio, 1),
    }
    
    return render(request, 'car/estadisticas_trabajos.html', context)

