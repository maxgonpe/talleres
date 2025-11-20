from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from datetime import timedelta, datetime
from decimal import Decimal

from .models import Trabajo, Diagnostico, AdministracionTaller, ResumenTrabajo, RegistroEvento, TrabajoAccion, TrabajoRepuesto, Componente, Accion, Repuesto
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
    # 1. ESTADÍSTICAS GENERALES (desde ResumenTrabajo - datos históricos persistentes)
    # ========================
    total_trabajos = ResumenTrabajo.objects.count()
    trabajos_activos = ResumenTrabajo.objects.exclude(estado_actual='entregado').count()
    trabajos_completados = ResumenTrabajo.objects.filter(estado_actual='completado').count()
    trabajos_entregados = ResumenTrabajo.objects.filter(estado_actual='entregado').count()
    
    # Trabajos por estado con porcentajes (desde ResumenTrabajo)
    trabajos_por_estado_raw = ResumenTrabajo.objects.values('estado_actual').annotate(
        cantidad=Count('trabajo_id')
    ).order_by('estado_actual')
    
    trabajos_por_estado = []
    for estado_data in trabajos_por_estado_raw:
        porcentaje = (estado_data['cantidad'] / total_trabajos * 100) if total_trabajos > 0 else 0
        trabajos_por_estado.append({
            'estado': estado_data['estado_actual'],
            'cantidad': estado_data['cantidad'],
            'porcentaje': round(porcentaje, 1)
        })
    
    # ========================
    # 2. TIEMPOS DE RESPUESTA (desde RegistroEvento - datos históricos persistentes)
    # ========================
    # Tiempo desde diagnóstico creado hasta aprobado usando eventos
    eventos_diagnostico_creado = RegistroEvento.objects.filter(
        tipo_evento='diagnostico_creado'
    ).select_related().order_by('diagnostico_id', 'fecha_evento')
    
    eventos_diagnostico_aprobado = RegistroEvento.objects.filter(
        tipo_evento='diagnostico_aprobado'
    ).select_related().order_by('diagnostico_id', 'fecha_evento')
    
    tiempos_respuesta = []
    # Crear diccionario de diagnósticos aprobados por ID
    aprobados_dict = {e.diagnostico_id: e.fecha_evento for e in eventos_diagnostico_aprobado if e.diagnostico_id}
    
    for evento_creado in eventos_diagnostico_creado:
        if evento_creado.diagnostico_id and evento_creado.diagnostico_id in aprobados_dict:
            fecha_creado = evento_creado.fecha_evento
            fecha_aprobado = aprobados_dict[evento_creado.diagnostico_id]
            delta = fecha_aprobado - fecha_creado
            tiempos_respuesta.append(delta.total_seconds() / 3600)  # En horas
    
    tiempo_respuesta_promedio = sum(tiempos_respuesta) / len(tiempos_respuesta) if tiempos_respuesta else 0
    
    # ========================
    # 3. TIEMPO EN CADA ETAPA (desde RegistroEvento - datos históricos persistentes)
    # ========================
    # Calcular tiempo en cada etapa usando eventos de cambio_estado e ingreso
    tiempos_etapas = {
        'iniciado': [],
        'trabajando': [],
        'completado': [],
        'entregado': []
    }
    
    # Obtener todos los eventos de ingreso y cambios de estado ordenados por trabajo y fecha
    eventos_ingreso = RegistroEvento.objects.filter(
        tipo_evento='ingreso',
        trabajo_id__isnull=False
    ).order_by('trabajo_id', 'fecha_evento')
    
    cambios_estado = RegistroEvento.objects.filter(
        tipo_evento='cambio_estado',
        estado_anterior__isnull=False,
        estado_nuevo__isnull=False,
        trabajo_id__isnull=False
    ).order_by('trabajo_id', 'fecha_evento')
    
    # Crear diccionario de eventos por trabajo
    trabajos_eventos = {}
    for ingreso in eventos_ingreso:
        if ingreso.trabajo_id:
            if ingreso.trabajo_id not in trabajos_eventos:
                trabajos_eventos[ingreso.trabajo_id] = []
            trabajos_eventos[ingreso.trabajo_id].append({
                'tipo': 'ingreso',
                'estado': 'iniciado',
                'fecha': ingreso.fecha_evento
            })
    
    for cambio in cambios_estado:
        if cambio.trabajo_id:
            if cambio.trabajo_id not in trabajos_eventos:
                trabajos_eventos[cambio.trabajo_id] = []
            trabajos_eventos[cambio.trabajo_id].append({
                'tipo': 'cambio',
                'estado_anterior': cambio.estado_anterior,
                'estado_nuevo': cambio.estado_nuevo,
                'fecha': cambio.fecha_evento
            })
    
    # Calcular tiempos en cada etapa
    for trabajo_id, eventos in trabajos_eventos.items():
        eventos_ordenados = sorted(eventos, key=lambda x: x['fecha'])
        estado_actual = None
        fecha_inicio_estado = None
        
        for evento in eventos_ordenados:
            if evento['tipo'] == 'ingreso':
                estado_actual = 'iniciado'
                fecha_inicio_estado = evento['fecha']
            elif evento['tipo'] == 'cambio':
                # Si había un estado previo, calcular tiempo en ese estado
                if estado_actual and fecha_inicio_estado and estado_actual in tiempos_etapas:
                    delta = evento['fecha'] - fecha_inicio_estado
                    tiempos_etapas[estado_actual].append(delta.days)
                
                # Actualizar al nuevo estado
                estado_actual = evento['estado_nuevo']
                fecha_inicio_estado = evento['fecha']
    
    # Si un trabajo terminó en un estado, usar fecha actual o fecha_entrega del resumen
    # (esto se puede mejorar con eventos de entrega)
    
    dias_promedio_por_etapa = {
        estado: sum(tiempos) / len(tiempos) if tiempos else 0
        for estado, tiempos in tiempos_etapas.items()
    }
    
    # Días promedio en el taller (desde ResumenTrabajo - campo almacenado históricamente)
    dias_promedio_taller = ResumenTrabajo.objects.aggregate(
        promedio=Avg('dias_en_taller')
    )['promedio'] or 0
    
    # ========================
    # 4. VEHÍCULOS INGRESADOS (desde ResumenTrabajo y RegistroEvento - datos históricos)
    # ========================
    # Contar ingresos desde ResumenTrabajo (fecha_ingreso almacenada)
    vehiculos_semana = ResumenTrabajo.objects.filter(
        fecha_ingreso__gte=inicio_semana
    ).count()
    
    vehiculos_mes = ResumenTrabajo.objects.filter(
        fecha_ingreso__gte=inicio_mes
    ).count()
    
    # Promedio semanal (últimas 4 semanas) - desde ResumenTrabajo
    semanas_anteriores = []
    for i in range(4):
        inicio_sem = inicio_semana - timedelta(weeks=i+1)
        fin_sem = inicio_semana - timedelta(weeks=i)
        vehiculos_sem = ResumenTrabajo.objects.filter(
            fecha_ingreso__gte=inicio_sem,
            fecha_ingreso__lt=fin_sem
        ).count()
        semanas_anteriores.append(vehiculos_sem)
    
    promedio_semanal = sum(semanas_anteriores) / len(semanas_anteriores) if semanas_anteriores else 0
    
    # ========================
    # 5. UTILIDAD Y FINANCIERO (desde ResumenTrabajo - datos históricos persistentes)
    # ========================
    # Totales financieros desde ResumenTrabajo (campos almacenados)
    totales_financieros = ResumenTrabajo.objects.aggregate(
        total_mano_obra=Sum('total_mano_obra'),
        total_repuestos=Sum('total_repuestos')
    )
    
    total_mano_obra = totales_financieros['total_mano_obra'] or Decimal('0')
    total_repuestos = totales_financieros['total_repuestos'] or Decimal('0')
    total_ingresos = total_mano_obra + total_repuestos
    
    # Promedio por trabajo
    promedio_mano_obra = total_mano_obra / total_trabajos if total_trabajos > 0 else Decimal('0')
    promedio_repuestos = total_repuestos / total_trabajos if total_trabajos > 0 else Decimal('0')
    promedio_ingresos = total_ingresos / total_trabajos if total_trabajos > 0 else Decimal('0')
    
    # Trabajos completados esta semana (usando eventos de entrega desde RegistroEvento)
    trabajos_completados_semana = RegistroEvento.objects.filter(
        tipo_evento='entrega',
        fecha_evento__gte=inicio_semana
    ).values('trabajo_id').distinct().count()
    
    # Ingresos de la semana (desde eventos de entrega con total_general almacenado)
    ingresos_semana_totales = RegistroEvento.objects.filter(
        tipo_evento='entrega',
        fecha_evento__gte=inicio_semana,
        total_general__isnull=False
    ).aggregate(total=Sum('total_general'))['total'] or Decimal('0')
    
    # Dividir ingresos de la semana entre mano de obra y repuestos usando proporciones
    # O usar eventos individuales con montos almacenados
    ingresos_semana_mano_obra = RegistroEvento.objects.filter(
        tipo_evento='entrega',
        fecha_evento__gte=inicio_semana,
        total_mano_obra__isnull=False
    ).aggregate(total=Sum('total_mano_obra'))['total'] or Decimal('0')
    
    ingresos_semana_repuestos = RegistroEvento.objects.filter(
        tipo_evento='entrega',
        fecha_evento__gte=inicio_semana,
        total_repuestos__isnull=False
    ).aggregate(total=Sum('total_repuestos'))['total'] or Decimal('0')
    
    ingresos_semana = ingresos_semana_mano_obra + ingresos_semana_repuestos
    
    # ========================
    # 6. PORCENTAJE DE AVANCE (desde ResumenTrabajo - campo almacenado)
    # ========================
    # Promedio de avance desde ResumenTrabajo
    promedio_avance = ResumenTrabajo.objects.aggregate(
        promedio=Avg('porcentaje_avance')
    )['promedio'] or 0
    
    # Trabajos por rango de avance con porcentajes (usando consultas agregadas)
    avance_0_25 = ResumenTrabajo.objects.filter(
        porcentaje_avance__gte=0,
        porcentaje_avance__lt=25
    ).count()
    
    avance_25_50 = ResumenTrabajo.objects.filter(
        porcentaje_avance__gte=25,
        porcentaje_avance__lt=50
    ).count()
    
    avance_50_75 = ResumenTrabajo.objects.filter(
        porcentaje_avance__gte=50,
        porcentaje_avance__lt=75
    ).count()
    
    avance_75_100 = ResumenTrabajo.objects.filter(
        porcentaje_avance__gte=75,
        porcentaje_avance__lte=100
    ).count()
    
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
    
    # ========================
    # 8. ACCIONES RESUELTAS EN EL PERÍODO (NUEVO)
    # ========================
    # Obtener período desde request (por defecto: último mes)
    periodo_dias = int(request.GET.get('periodo', 30))
    fecha_inicio_periodo = ahora - timedelta(days=periodo_dias)
    
    # Acciones completadas en el período
    acciones_completadas = TrabajoAccion.objects.filter(
        completado=True,
        fecha__gte=fecha_inicio_periodo
    ).select_related('accion', 'componente', 'trabajo')
    
    # Obtener todas las acciones con sus datos para calcular subtotales
    acciones_detalle = list(acciones_completadas.values(
        'accion__nombre', 
        'componente__nombre',
        'accion_id',
        'componente_id',
        'precio_mano_obra',
        'cantidad'
    ))
    
    # Agrupar y calcular en Python
    acciones_agrupadas = {}
    for acc in acciones_detalle:
        clave = (acc['accion_id'], acc['componente_id'])
        if clave not in acciones_agrupadas:
            acciones_agrupadas[clave] = {
                'accion_nombre': acc['accion__nombre'],
                'componente_nombre': acc['componente__nombre'],
                'accion_id': acc['accion_id'],
                'componente_id': acc['componente_id'],
                'recurrencias': 0,
                'cantidad_total': 0,
                'total_ingresos': Decimal('0')
            }
        
        subtotal = Decimal(str(acc['precio_mano_obra'])) * Decimal(str(acc['cantidad']))
        acciones_agrupadas[clave]['recurrencias'] += 1
        acciones_agrupadas[clave]['cantidad_total'] += acc['cantidad']
        acciones_agrupadas[clave]['total_ingresos'] += subtotal
    
    # Convertir a lista y ordenar
    acciones_resueltas_lista = sorted(
        acciones_agrupadas.values(),
        key=lambda x: x['recurrencias'],
        reverse=True
    )
    
    # ========================
    # 9. INGRESOS POR ACCIÓN (MÁS RENTABLE A MENOS RENTABLE) (NUEVO)
    # ========================
    # Obtener datos de acciones con trabajos para calcular ingresos
    acciones_con_trabajos = list(acciones_completadas.values(
        'accion__nombre',
        'accion_id',
        'trabajo_id',
        'precio_mano_obra',
        'cantidad'
    ))
    
    # Agrupar por acción y calcular en Python
    ingresos_agrupados = {}
    trabajos_por_accion = {}
    
    for acc in acciones_con_trabajos:
        accion_id = acc['accion_id']
        trabajo_id = acc['trabajo_id']
        
        if accion_id not in ingresos_agrupados:
            ingresos_agrupados[accion_id] = {
                'accion_nombre': acc['accion__nombre'],
                'total_ingresos': Decimal('0'),
                'cantidad_veces': 0,
                'cantidad_total': 0
            }
            trabajos_por_accion[accion_id] = set()
        
        subtotal = Decimal(str(acc['precio_mano_obra'])) * Decimal(str(acc['cantidad']))
        ingresos_agrupados[accion_id]['total_ingresos'] += subtotal
        ingresos_agrupados[accion_id]['cantidad_veces'] += 1
        ingresos_agrupados[accion_id]['cantidad_total'] += acc['cantidad']
        trabajos_por_accion[accion_id].add(trabajo_id)
    
    # Formatear para el template
    ingresos_por_accion_lista = []
    for accion_id, datos in ingresos_agrupados.items():
        cantidad_trabajos = len(trabajos_por_accion[accion_id])
        ingresos_por_accion_lista.append({
            'accion_nombre': datos['accion_nombre'],
            'total_ingresos': datos['total_ingresos'],
            'cantidad_trabajos': cantidad_trabajos,
            'cantidad_veces': datos['cantidad_veces'],
            'cantidad_total': datos['cantidad_total'],
            'promedio_por_trabajo': (datos['total_ingresos'] / cantidad_trabajos) if cantidad_trabajos > 0 else Decimal('0')
        })
    
    # Ordenar por total_ingresos descendente
    ingresos_por_accion_lista.sort(key=lambda x: x['total_ingresos'], reverse=True)
    
    # ========================
    # 10. CONCENTRACIÓN DE REPARACIONES POR COMPONENTE (NUEVO)
    # ========================
    # Obtener datos de componentes con trabajos
    componentes_con_trabajos = list(acciones_completadas.values(
        'componente__nombre',
        'componente_id',
        'trabajo_id',
        'precio_mano_obra',
        'cantidad'
    ))
    
    # Agrupar por componente y calcular en Python
    componentes_agrupados = {}
    trabajos_por_componente = {}
    
    for comp in componentes_con_trabajos:
        componente_id = comp['componente_id']
        trabajo_id = comp['trabajo_id']
        
        if componente_id not in componentes_agrupados:
            componentes_agrupados[componente_id] = {
                'componente_nombre': comp['componente__nombre'],
                'cantidad_acciones': 0,
                'total_ingresos': Decimal('0')
            }
            trabajos_por_componente[componente_id] = set()
        
        subtotal = Decimal(str(comp['precio_mano_obra'])) * Decimal(str(comp['cantidad']))
        componentes_agrupados[componente_id]['cantidad_acciones'] += 1
        componentes_agrupados[componente_id]['total_ingresos'] += subtotal
        trabajos_por_componente[componente_id].add(trabajo_id)
    
    # Calcular total de trabajos únicos en el período
    total_trabajos_periodo = len(set(comp['trabajo_id'] for comp in componentes_con_trabajos))
    
    # Formatear para el template
    reparaciones_por_componente_lista = []
    for componente_id, datos in componentes_agrupados.items():
        cantidad_trabajos = len(trabajos_por_componente[componente_id])
        porcentaje = (cantidad_trabajos / total_trabajos_periodo * 100) if total_trabajos_periodo > 0 else 0
        reparaciones_por_componente_lista.append({
            'componente_nombre': datos['componente_nombre'],
            'cantidad_trabajos': cantidad_trabajos,
            'cantidad_acciones': datos['cantidad_acciones'],
            'total_ingresos': datos['total_ingresos'],
            'porcentaje': round(porcentaje, 1),
            'componente_id': componente_id
        })
    
    # Ordenar por cantidad_trabajos descendente
    reparaciones_por_componente_lista.sort(key=lambda x: x['cantidad_trabajos'], reverse=True)
    
    # ========================
    # 11. REPUESTOS MÁS USADOS Y RECURRENTES (NUEVO)
    # ========================
    # Repuestos completados en el período
    repuestos_completados = TrabajoRepuesto.objects.filter(
        completado=True,
        fecha__gte=fecha_inicio_periodo
    ).select_related('repuesto', 'repuesto_externo', 'componente', 'trabajo')
    
    # Agrupar por repuesto (tanto internos como externos)
    repuestos_usados = repuestos_completados.values(
        'repuesto__nombre',
        'repuesto__sku',
        'repuesto_id',
        'repuesto_externo__nombre',
        'repuesto_externo_id'
    ).annotate(
        cantidad_veces=Count('id'),
        cantidad_total=Sum('cantidad'),
        total_ingresos=Sum('subtotal'),
        cantidad_trabajos=Count('trabajo_id', distinct=True)
    ).order_by('-cantidad_veces')
    
    repuestos_usados_lista = []
    for rep in repuestos_usados:
        nombre = rep['repuesto__nombre'] if rep['repuesto__nombre'] else rep['repuesto_externo__nombre'] or 'Repuesto Externo'
        sku = rep['repuesto__sku'] or 'N/A'
        repuesto_id = rep['repuesto_id'] or rep['repuesto_externo_id']
        
        repuestos_usados_lista.append({
            'nombre': nombre,
            'sku': sku,
            'cantidad_veces': rep['cantidad_veces'],
            'cantidad_total': rep['cantidad_total'],
            'total_ingresos': rep['total_ingresos'] or Decimal('0'),
            'cantidad_trabajos': rep['cantidad_trabajos'],
            'promedio_por_trabajo': (rep['total_ingresos'] / rep['cantidad_trabajos']) if rep['cantidad_trabajos'] > 0 else Decimal('0'),
            'repuesto_id': repuesto_id
        })
    
    # Ordenar por recurrencia (cantidad_veces) y luego por ingresos
    repuestos_usados_lista.sort(key=lambda x: (x['cantidad_veces'], x['total_ingresos']), reverse=True)
    
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
        
        # Nuevas estadísticas detalladas
        'periodo_dias': periodo_dias,
        'fecha_inicio_periodo': fecha_inicio_periodo,
        'acciones_resueltas': acciones_resueltas_lista,
        'ingresos_por_accion': ingresos_por_accion_lista,
        'reparaciones_por_componente': reparaciones_por_componente_lista,
        'repuestos_usados': repuestos_usados_lista,
        'total_trabajos_periodo': total_trabajos_periodo,
    }
    
    return render(request, 'car/estadisticas_trabajos.html', context)

