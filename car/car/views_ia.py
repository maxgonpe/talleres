from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.conf import settings
import requests
import json
import logging
from functools import wraps
from .agent import Agent
from .models import Trabajo, Cliente_Taller, Vehiculo, Repuesto, Diagnostico, TrabajoAccion, TrabajoRepuesto, TrabajoAbono, Mecanico, BonoGenerado, PagoMecanico, ConfiguracionBonoMecanico, Componente, Accion, ComponenteAccion, Compra, CompraItem, VehiculoVersion, RepuestoAplicacion, RepuestoEnStock

# Configurar logging
logger = logging.getLogger(__name__)

def ajax_login_required(view_func):
    """Decorador que devuelve JSON en lugar de redirigir a login para peticiones AJAX"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Detectar si es petición AJAX o JSON
            is_ajax = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                request.content_type == 'application/json' or
                'application/json' in request.headers.get('Accept', '')
            )
            if is_ajax:
                return JsonResponse({"error": "No autenticado. Por favor inicia sesión."}, status=401)
            # Si no es AJAX, usar el comportamiento normal de login_required
            from django.contrib.auth.decorators import login_required
            return login_required(view_func)(request, *args, **kwargs)
        return view_func(request, *args, **kwargs)
    return wrapper


def query_sistema_data(tipo, filtro=None, detalle=False):
    """
    Consulta información del sistema del taller mecánico
    
    Args:
        tipo: Tipo de consulta (trabajo, cliente, vehiculo, repuesto, estadisticas)
        filtro: Filtro opcional de búsqueda
        detalle: Si se requiere información detallada
    
    Returns:
        dict: Información consultada del sistema
    """
    try:
        from django.db import connection
        # Verificar conexión a la base de datos
        connection.ensure_connection()
        if tipo == "trabajo":
            trabajos = Trabajo.objects.filter(visible=True)
            
            if filtro:
                # Intentar buscar por ID
                try:
                    trabajo_id = int(filtro)
                    trabajos = trabajos.filter(id=trabajo_id)
                except ValueError:
                    # Buscar por placa del vehículo
                    trabajos = trabajos.filter(vehiculo__placa__icontains=filtro)
            
            trabajos = trabajos.order_by('-fecha_inicio')[:10]
            
            if detalle:
                datos = []
                for t in trabajos:
                    datos.append({
                        "id": t.id,
                        "vehiculo": str(t.vehiculo),
                        "cliente": t.vehiculo.cliente.nombre,
                        "estado": t.get_estado_display(),
                        "fecha_inicio": t.fecha_inicio.strftime("%Y-%m-%d %H:%M"),
                        "total_presupuestado": float(t.total_general),
                        "mecanicos": [str(m) for m in t.mecanicos.all()]
                    })
            else:
                datos = {
                    "total": trabajos.count(),
                    "activos": trabajos.filter(estado__in=["iniciado", "trabajando"]).count(),
                    "completados": trabajos.filter(estado="completado").count(),
                    "entregados": trabajos.filter(estado="entregado").count(),
                    "ultimos": [{"id": t.id, "vehiculo": str(t.vehiculo), "estado": t.get_estado_display()} for t in trabajos[:5]]
                }
            
            return {"tipo": "trabajo", "datos": datos}
        
        elif tipo == "cliente":
            clientes = Cliente_Taller.objects.filter(activo=True)
            
            if filtro:
                # Buscar por RUT o nombre
                clientes = clientes.filter(
                    Q(rut__icontains=filtro) | Q(nombre__icontains=filtro)
                )
            
            clientes = clientes.order_by('nombre')[:20]
            
            if detalle:
                datos = []
                for c in clientes:
                    vehiculos_count = Vehiculo.objects.filter(cliente=c).count()
                    trabajos_count = Trabajo.objects.filter(vehiculo__cliente=c, visible=True).count()
                    datos.append({
                        "rut": c.rut,
                        "nombre": c.nombre,
                        "telefono": c.telefono or "N/A",
                        "email": c.email or "N/A",
                        "vehiculos": vehiculos_count,
                        "trabajos": trabajos_count
                    })
            else:
                datos = {
                    "total": clientes.count(),
                    "lista": [{"rut": c.rut, "nombre": c.nombre} for c in clientes[:10]]
                }
            
            return {"tipo": "cliente", "datos": datos}
        
        elif tipo == "vehiculo":
            vehiculos = Vehiculo.objects.all()
            
            if filtro:
                # Buscar por placa o cliente
                vehiculos = vehiculos.filter(
                    Q(placa__icontains=filtro) | Q(cliente__nombre__icontains=filtro) | Q(cliente__rut__icontains=filtro)
                )
            
            vehiculos = vehiculos.order_by('-id')[:20]
            
            if detalle:
                datos = []
                for v in vehiculos:
                    trabajos_count = Trabajo.objects.filter(vehiculo=v, visible=True).count()
                    datos.append({
                        "placa": v.placa,
                        "marca": v.marca,
                        "modelo": v.modelo,
                        "anio": v.anio,
                        "cliente": v.cliente.nombre,
                        "cliente_rut": v.cliente.rut,
                        "trabajos": trabajos_count
                    })
            else:
                datos = {
                    "total": vehiculos.count(),
                    "lista": [{"placa": v.placa, "vehiculo": f"{v.marca} {v.modelo} ({v.anio})", "cliente": v.cliente.nombre} for v in vehiculos[:10]]
                }
            
            return {"tipo": "vehiculo", "datos": datos}
        
        elif tipo == "repuesto":
            # Solo contar registros - sin filtros ni procesamiento adicional
            total_real = Repuesto.objects.all().count()
            
            # Si hay filtro, aplicar filtro y contar
            if filtro:
                repuestos_filtrados = Repuesto.objects.filter(
                    Q(nombre__icontains=filtro) | 
                    Q(codigo_barra__icontains=filtro) | 
                    Q(sku__icontains=filtro) |
                    Q(marca__icontains=filtro) |
                    Q(referencia__icontains=filtro) |
                    Q(descripcion__icontains=filtro)
                )
                total_real = repuestos_filtrados.count()
            
            # Solo devolver el count total
            return {
                "tipo": "repuesto", 
                "datos": {
                    "total": total_real
                }
            }
        
        elif tipo == "estadisticas":
            ahora = timezone.now()
            hoy = ahora.date()
            
            trabajos_activos = Trabajo.objects.filter(visible=True, estado__in=["iniciado", "trabajando"]).count()
            trabajos_hoy = Trabajo.objects.filter(visible=True, fecha_inicio__date=hoy).count()
            trabajos_completados = Trabajo.objects.filter(visible=True, estado="completado").count()
            
            clientes_total = Cliente_Taller.objects.filter(activo=True).count()
            vehiculos_total = Vehiculo.objects.count()
            repuestos_total = Repuesto.objects.count()
            
            diagnosticos_hoy = Diagnostico.objects.filter(fecha_creacion__date=hoy).count()
            
            datos = {
                "trabajos": {
                    "activos": trabajos_activos,
                    "hoy": trabajos_hoy,
                    "completados": trabajos_completados
                },
                "clientes": clientes_total,
                "vehiculos": vehiculos_total,
                "repuestos": repuestos_total,
                "diagnosticos_hoy": diagnosticos_hoy
            }
            
            return {"tipo": "estadisticas", "datos": datos}
        
        else:
            return {"error": f"Tipo de consulta no válido: {tipo}"}
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error en query_sistema_data: {error_type}: {error_msg}", exc_info=True)
        return {
            "error": f"Error al consultar sistema: {error_msg}",
            "error_type": error_type,
            "success": False
        }


def listado_trabajos_data(estado="todos", limite=20):
    """
    Lista todos los trabajos del taller con todos sus campos y detalles
    
    Args:
        estado: Filtro por estado (todos, activos, completados, entregados, iniciado, trabajando)
        limite: Número máximo de trabajos a listar
    
    Returns:
        dict: Lista de trabajos con todos sus campos
    """
    try:
        from django.db import connection
        # Verificar conexión a la base de datos
        connection.ensure_connection()
        trabajos = Trabajo.objects.filter(visible=True)
        
        # Aplicar filtro por estado
        if estado == "activos":
            trabajos = trabajos.filter(estado__in=["iniciado", "trabajando"])
        elif estado != "todos":
            trabajos = trabajos.filter(estado=estado)
        
        # Ordenar por fecha más reciente y limitar
        trabajos = trabajos.order_by('-fecha_inicio')[:limite]
        
        # Construir lista con todos los campos
        lista_trabajos = []
        for t in trabajos:
            try:
                # Obtener información del vehículo (verificar que existe)
                vehiculo = t.vehiculo
                if not vehiculo:
                    logger.warning(f"Trabajo {t.id} no tiene vehículo asociado")
                    continue
                
                # Obtener información del cliente (verificar que existe)
                try:
                    cliente = vehiculo.cliente
                    if not cliente:
                        logger.warning(f"Vehículo {vehiculo.id} no tiene cliente asociado")
                        cliente_data = {
                            "rut": "N/A",
                            "nombre": "Cliente no encontrado",
                            "telefono": "N/A",
                            "email": "N/A"
                        }
                    else:
                        cliente_data = {
                            "rut": cliente.rut or "N/A",
                            "nombre": cliente.nombre or "N/A",
                            "telefono": cliente.telefono or "N/A",
                            "email": cliente.email or "N/A"
                        }
                except Exception as e_cliente:
                    logger.warning(f"Error obteniendo cliente para vehículo {vehiculo.id}: {str(e_cliente)}")
                    cliente_data = {
                        "rut": "N/A",
                        "nombre": "Error al obtener cliente",
                        "telefono": "N/A",
                        "email": "N/A"
                    }
            
                # Obtener mecánicos asignados
                mecanicos = []
                try:
                    for m in t.mecanicos.all():
                        try:
                            if hasattr(m, 'user') and m.user:
                                nombre = m.user.get_full_name() or m.user.username
                            else:
                                nombre = f"Mecanico-{m.id}"
                            mecanicos.append({"id": m.id, "nombre": nombre})
                        except Exception as e_mec:
                            logger.warning(f"Error procesando mecánico {m.id if hasattr(m, 'id') else 'N/A'}: {str(e_mec)}")
                            mecanicos.append({"id": m.id if hasattr(m, 'id') else 0, "nombre": f"Mecanico-{m.id if hasattr(m, 'id') else 'N/A'}"})
                except Exception as e_mecanicos:
                    logger.warning(f"Error obteniendo mecánicos para trabajo {t.id}: {str(e_mecanicos)}")
                    mecanicos = []
            
                # Obtener acciones del trabajo
                acciones = []
                try:
                    for accion in t.acciones.all():
                        try:
                            acciones.append({
                                "id": accion.id,
                                "componente": accion.componente.nombre if accion.componente else "N/A",
                                "accion": accion.accion.nombre if accion.accion else "N/A",
                                "cantidad": float(accion.cantidad) if accion.cantidad else 0.0,
                                "precio_unitario": float(accion.precio_mano_obra) if accion.precio_mano_obra else 0.0,
                                "subtotal": float(accion.subtotal) if accion.subtotal else 0.0,
                                "completado": accion.completado if hasattr(accion, 'completado') else False
                            })
                        except Exception as e_acc:
                            logger.warning(f"Error procesando acción {accion.id if hasattr(accion, 'id') else 'N/A'}: {str(e_acc)}")
                            continue
                except Exception as e_acciones:
                    logger.warning(f"Error obteniendo acciones para trabajo {t.id}: {str(e_acciones)}")
                    acciones = []
            
                # Obtener repuestos del trabajo
                repuestos = []
                try:
                    for repuesto in t.repuestos.all():
                        try:
                            repuestos.append({
                                "id": repuesto.id,
                                "repuesto": repuesto.repuesto.nombre if repuesto.repuesto else "N/A",
                                "cantidad": float(repuesto.cantidad) if repuesto.cantidad else 0.0,
                                "precio_unitario": float(repuesto.precio_unitario) if repuesto.precio_unitario else 0.0,
                                "subtotal": float(repuesto.subtotal) if repuesto.subtotal else 0.0,
                                "completado": repuesto.completado if hasattr(repuesto, 'completado') else False
                            })
                        except Exception as e_rep:
                            logger.warning(f"Error procesando repuesto {repuesto.id if hasattr(repuesto, 'id') else 'N/A'}: {str(e_rep)}")
                            continue
                except Exception as e_repuestos:
                    logger.warning(f"Error obteniendo repuestos para trabajo {t.id}: {str(e_repuestos)}")
                    repuestos = []
            
                # Obtener abonos
                abonos = []
                try:
                    for abono in t.abonos.all():
                        try:
                            abonos.append({
                                "id": abono.id,
                                "fecha": abono.fecha.strftime("%Y-%m-%d") if abono.fecha else None,
                                "monto": float(abono.monto) if abono.monto else 0.0,
                                "descripcion": abono.descripcion or "",
                                "metodo_pago": abono.metodo_pago if hasattr(abono, 'metodo_pago') else "N/A",
                                "metodo_pago_display": abono.get_metodo_pago_display() if hasattr(abono, 'get_metodo_pago_display') else "N/A"
                            })
                        except Exception as e_abono:
                            logger.warning(f"Error procesando abono {abono.id if hasattr(abono, 'id') else 'N/A'}: {str(e_abono)}")
                            continue
                except Exception as e_abonos:
                    logger.warning(f"Error obteniendo abonos para trabajo {t.id}: {str(e_abonos)}")
                    abonos = []
            
                trabajo_data = {
                    "id": t.id,
                    "vehiculo": {
                        "placa": vehiculo.placa or "N/A",
                        "marca": vehiculo.marca or "N/A",
                        "modelo": vehiculo.modelo or "N/A",
                        "anio": vehiculo.anio or "N/A",
                        "vin": vehiculo.vin or "N/A",
                        "descripcion_motor": vehiculo.descripcion_motor or "N/A"
                    },
                    "cliente": cliente_data,
                    "fecha_inicio": t.fecha_inicio.strftime("%Y-%m-%d %H:%M:%S") if t.fecha_inicio else None,
                    "fecha_fin": t.fecha_fin.strftime("%Y-%m-%d %H:%M:%S") if t.fecha_fin else None,
                    "estado": t.estado,
                    "estado_display": t.get_estado_display() if hasattr(t, 'get_estado_display') else str(t.estado),
                    "observaciones": t.observaciones or "" if hasattr(t, 'observaciones') else "",
                    "kilometraje_actual": t.lectura_kilometraje_actual if hasattr(t, 'lectura_kilometraje_actual') else None,
                    "mecanicos": mecanicos,
                    "totales": {
                        "total_mano_obra": float(t.total_mano_obra) if hasattr(t, 'total_mano_obra') and t.total_mano_obra else 0.0,
                        "total_repuestos": float(t.total_repuestos) if hasattr(t, 'total_repuestos') and t.total_repuestos else 0.0,
                        "total_adicionales": float(t.total_adicionales) if hasattr(t, 'total_adicionales') and t.total_adicionales else 0.0,
                        "total_descuentos": float(t.total_descuentos) if hasattr(t, 'total_descuentos') and t.total_descuentos else 0.0,
                        "total_presupuestado": float(t.total_general) if hasattr(t, 'total_general') and t.total_general else 0.0,
                        "total_realizado_mano_obra": float(t.total_realizado_mano_obra) if hasattr(t, 'total_realizado_mano_obra') and t.total_realizado_mano_obra else 0.0,
                        "total_realizado_repuestos": float(t.total_realizado_repuestos) if hasattr(t, 'total_realizado_repuestos') and t.total_realizado_repuestos else 0.0,
                        "total_realizado": float(t.total_realizado) if hasattr(t, 'total_realizado') and t.total_realizado else 0.0,
                        "total_abonos": float(t.total_abonos) if hasattr(t, 'total_abonos') and t.total_abonos else 0.0,
                        "saldo_pendiente": float((t.total_general or 0) - (t.total_abonos or 0))
                    },
                    "acciones": acciones,
                    "repuestos": repuestos,
                    "abonos": abonos,
                    "cantidad_acciones": len(acciones),
                    "cantidad_repuestos": len(repuestos),
                    "cantidad_abonos": len(abonos)
                }
                
                lista_trabajos.append(trabajo_data)
            except Exception as e_trabajo:
                logger.error(f"Error procesando trabajo {t.id if hasattr(t, 'id') else 'N/A'}: {str(e_trabajo)}", exc_info=True)
                continue
        
        return {
            "total_encontrados": len(lista_trabajos),
            "estado_filtro": estado,
            "trabajos": lista_trabajos
        }
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error en listado_trabajos_data: {error_type}: {error_msg}", exc_info=True)
        return {
            "error": f"Error al listar trabajos: {error_msg}",
            "error_type": error_type,
            "success": False
        }


def listado_mecanicos_data(activo=None, limite=50):
    """
    Lista todos los mecánicos del taller con todos sus campos y detalles
    
    Args:
        activo: Filtro por estado activo (True, False, None para todos)
        limite: Número máximo de mecánicos a listar
    
    Returns:
        dict: Lista de mecánicos con todos sus campos
    """
    try:
        from django.db import connection
        # Verificar conexión a la base de datos
        connection.ensure_connection()
        mecanicos = Mecanico.objects.all()
        
        # Aplicar filtro por estado activo
        if activo is not None:
            mecanicos = mecanicos.filter(activo=activo)
        
        # Ordenar por fecha de ingreso y limitar
        mecanicos = mecanicos.order_by('-fecha_ingreso')[:limite]
        
        # Construir lista con todos los campos
        lista_mecanicos = []
        for m in mecanicos:
            # Obtener información del usuario (verificar que existe)
            try:
                user = m.user
                if not user:
                    # Si no hay usuario, crear datos básicos
                    usuario_data = {
                        "username": f"mecanico_{m.id}",
                        "first_name": "",
                        "last_name": "",
                        "email": "N/A",
                        "is_active": False,
                        "date_joined": None
                    }
                    user = None  # Marcar como None para usar datos básicos
                else:
                    usuario_data = {
                        "username": user.username,
                        "first_name": user.first_name or "",
                        "last_name": user.last_name or "",
                        "email": user.email or "N/A",
                        "is_active": user.is_active,
                        "date_joined": user.date_joined.strftime("%Y-%m-%d %H:%M:%S") if user.date_joined else None
                    }
            except Exception as e_user:
                logger.warning(f"Error obteniendo usuario para mecánico {m.id}: {str(e_user)}")
                usuario_data = {
                    "username": f"mecanico_{m.id}",
                    "first_name": "",
                    "last_name": "",
                    "email": "N/A",
                    "is_active": False,
                    "date_joined": None
                }
                user = None
            
            # Obtener configuración de bono si existe
            config_bono = None
            try:
                config = m.configuracion_bono
                config_bono = {
                    "activo": config.activo,
                    "tipo_bono": config.tipo_bono,
                    "tipo_bono_display": config.get_tipo_bono_display(),
                    "porcentaje_mano_obra": float(config.porcentaje_mano_obra) if config.porcentaje_mano_obra else None,
                    "cantidad_fija": float(config.cantidad_fija) if config.cantidad_fija else None
                }
            except ConfiguracionBonoMecanico.DoesNotExist:
                pass
            
            # Obtener bonos generados
            bonos = BonoGenerado.objects.filter(mecanico=m).order_by('-fecha_generacion')[:10]
            bonos_lista = []
            for bono in bonos:
                bonos_lista.append({
                    "id": bono.id,
                    "trabajo_id": bono.trabajo.id if bono.trabajo else None,
                    "monto": float(bono.monto),
                    "fecha_generacion": bono.fecha_generacion.strftime("%Y-%m-%d %H:%M:%S") if bono.fecha_generacion else None,
                    "pagado": bono.pagado,
                    "fecha_pago": bono.fecha_pago.strftime("%Y-%m-%d %H:%M:%S") if bono.fecha_pago else None
                })
            
            # Obtener pagos realizados
            pagos = PagoMecanico.objects.filter(mecanico=m).order_by('-fecha_pago')[:10]
            pagos_lista = []
            for pago in pagos:
                pagos_lista.append({
                    "id": pago.id,
                    "monto": float(pago.monto),
                    "metodo_pago": pago.metodo_pago,
                    "metodo_pago_display": pago.get_metodo_pago_display(),
                    "fecha_pago": pago.fecha_pago.strftime("%Y-%m-%d %H:%M:%S") if pago.fecha_pago else None,
                    "notas": pago.notas or ""
                })
            
            # Obtener trabajos asignados (últimos 10)
            try:
                trabajos_asignados = Trabajo.objects.filter(mecanicos=m, visible=True).order_by('-fecha_inicio')[:10]
                trabajos_lista = []
                for trabajo in trabajos_asignados:
                    try:
                        trabajos_lista.append({
                            "id": trabajo.id,
                            "vehiculo": str(trabajo.vehiculo) if trabajo.vehiculo else "N/A",
                            "estado": trabajo.estado,
                            "estado_display": trabajo.get_estado_display(),
                            "fecha_inicio": trabajo.fecha_inicio.strftime("%Y-%m-%d %H:%M:%S") if trabajo.fecha_inicio else None,
                            "total_presupuestado": float(trabajo.total_general) if trabajo.total_general else 0.0
                        })
                    except Exception as e_trab:
                        logger.warning(f"Error procesando trabajo {trabajo.id if hasattr(trabajo, 'id') else 'N/A'} para mecánico {m.id}: {str(e_trab)}")
                        continue
            except Exception as e_trabajos:
                logger.warning(f"Error obteniendo trabajos para mecánico {m.id}: {str(e_trabajos)}")
                trabajos_asignados = []
                trabajos_lista = []
            
            # Calcular estadísticas (con manejo de errores)
            try:
                total_bonos = float(m.saldo_bonos_total) if hasattr(m, 'saldo_bonos_total') and m.saldo_bonos_total else 0.0
            except:
                total_bonos = 0.0
            try:
                bonos_pendientes = float(m.saldo_bonos_pendiente) if hasattr(m, 'saldo_bonos_pendiente') and m.saldo_bonos_pendiente else 0.0
            except:
                bonos_pendientes = 0.0
            try:
                total_pagado = sum([float(pago.monto) for pago in pagos])
            except:
                total_pagado = 0.0
            saldo_actual = bonos_pendientes - total_pagado
            
            mecanico_data = {
                "id": m.id,
                "usuario": usuario_data,
                "especialidad": m.especialidad or "N/A",
                "fecha_ingreso": m.fecha_ingreso.strftime("%Y-%m-%d") if m.fecha_ingreso else None,
                "activo": m.activo,
                "rol": m.rol,
                "rol_display": m.get_rol_display(),
                "permisos": {
                    "puede_ver_diagnosticos": m.puede_ver_diagnosticos,
                    "puede_ver_trabajos": m.puede_ver_trabajos,
                    "puede_ver_pos": m.puede_ver_pos,
                    "puede_ver_compras": m.puede_ver_compras,
                    "puede_ver_inventario": m.puede_ver_inventario,
                    "puede_ver_administracion": m.puede_ver_administracion,
                    "crear_clientes": m.crear_clientes,
                    "crear_vehiculos": m.crear_vehiculos,
                    "aprobar_diagnosticos": m.aprobar_diagnosticos,
                    "gestionar_usuarios": m.gestionar_usuarios
                },
                "configuracion_bono": config_bono,
                "estadisticas": {
                    "total_bonos_generados": total_bonos,
                    "bonos_pendientes": bonos_pendientes,
                    "total_pagado": total_pagado,
                    "saldo_actual": saldo_actual,
                    "cantidad_trabajos_asignados": len(trabajos_lista),
                    "cantidad_bonos": len(bonos_lista),
                    "cantidad_pagos": len(pagos_lista)
                },
                "bonos": bonos_lista,
                "pagos": pagos_lista,
                "trabajos_asignados": trabajos_lista
            }
            
            lista_mecanicos.append(mecanico_data)
        
        return {
            "total_encontrados": len(lista_mecanicos),
            "filtro_activo": activo,
            "mecanicos": lista_mecanicos
        }
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error en listado_mecanicos_data: {error_type}: {error_msg}", exc_info=True)
        return {
            "error": f"Error al listar mecánicos: {error_msg}",
            "error_type": error_type,
            "success": False
        }


def listado_clientes_data(activo=None, limite=50, filtro=None):
    """
    Lista todos los clientes del taller con todos sus campos y detalles
    
    Args:
        activo: Filtro por estado activo (True, False, None para todos)
        limite: Número máximo de clientes a listar
        filtro: Filtro de búsqueda por RUT o nombre
    
    Returns:
        dict: Lista de clientes con todos sus campos
    """
    try:
        from django.db import connection
        connection.ensure_connection()
        clientes = Cliente_Taller.objects.all()
        
        if activo is not None:
            clientes = clientes.filter(activo=activo)
        
        if filtro:
            clientes = clientes.filter(
                Q(rut__icontains=filtro) | Q(nombre__icontains=filtro)
            )
        
        clientes = clientes.order_by('nombre')[:limite]
        
        lista_clientes = []
        for c in clientes:
            try:
                vehiculos_count = Vehiculo.objects.filter(cliente=c).count()
                trabajos_count = Trabajo.objects.filter(vehiculo__cliente=c, visible=True).count()
                
                cliente_data = {
                    "rut": c.rut or "N/A",
                    "nombre": c.nombre or "N/A",
                    "telefono": c.telefono or "N/A",
                    "email": c.email or "N/A",
                    "direccion": c.direccion or "N/A",
                    "fecha_registro": c.fecha_registro.strftime("%Y-%m-%d %H:%M:%S") if c.fecha_registro else None,
                    "activo": c.activo,
                    "estadisticas": {
                        "vehiculos": vehiculos_count,
                        "trabajos": trabajos_count
                    }
                }
                lista_clientes.append(cliente_data)
            except Exception as e_cliente:
                logger.warning(f"Error procesando cliente {c.rut if hasattr(c, 'rut') else 'N/A'}: {str(e_cliente)}")
                continue
        
        return {
            "total_encontrados": len(lista_clientes),
            "filtro_activo": activo,
            "clientes": lista_clientes
        }
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error en listado_clientes_data: {error_type}: {error_msg}", exc_info=True)
        return {
            "error": f"Error al listar clientes: {error_msg}",
            "error_type": error_type,
            "success": False
        }


def listado_vehiculos_data(limite=50, filtro=None):
    """
    Lista todos los vehículos del taller con todos sus campos y detalles
    
    Args:
        limite: Número máximo de vehículos a listar
        filtro: Filtro de búsqueda por placa, marca, modelo o cliente
    
    Returns:
        dict: Lista de vehículos con todos sus campos
    """
    try:
        from django.db import connection
        connection.ensure_connection()
        vehiculos = Vehiculo.objects.all()
        
        if filtro:
            vehiculos = vehiculos.filter(
                Q(placa__icontains=filtro) | 
                Q(marca__icontains=filtro) | 
                Q(modelo__icontains=filtro) |
                Q(cliente__nombre__icontains=filtro) |
                Q(cliente__rut__icontains=filtro)
            )
        
        vehiculos = vehiculos.order_by('-id')[:limite]
        
        lista_vehiculos = []
        for v in vehiculos:
            try:
                trabajos_count = Trabajo.objects.filter(vehiculo=v, visible=True).count()
                diagnosticos_count = Diagnostico.objects.filter(vehiculo=v, visible=True).count()
                
                vehiculo_data = {
                    "id": v.id,
                    "placa": v.placa or "N/A",
                    "marca": v.marca or "N/A",
                    "modelo": v.modelo or "N/A",
                    "anio": v.anio or "N/A",
                    "vin": v.vin or "N/A",
                    "descripcion_motor": v.descripcion_motor or "N/A",
                    "cliente": {
                        "rut": v.cliente.rut if v.cliente else "N/A",
                        "nombre": v.cliente.nombre if v.cliente else "N/A"
                    },
                    "estadisticas": {
                        "trabajos": trabajos_count,
                        "diagnosticos": diagnosticos_count
                    }
                }
                lista_vehiculos.append(vehiculo_data)
            except Exception as e_vehiculo:
                logger.warning(f"Error procesando vehículo {v.id if hasattr(v, 'id') else 'N/A'}: {str(e_vehiculo)}")
                continue
        
        return {
            "total_encontrados": len(lista_vehiculos),
            "vehiculos": lista_vehiculos
        }
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error en listado_vehiculos_data: {error_type}: {error_msg}", exc_info=True)
        return {
            "error": f"Error al listar vehículos: {error_msg}",
            "error_type": error_type,
            "success": False
        }


def listado_componentes_data(activo=None, limite=100, filtro=None):
    """
    Lista todos los componentes del sistema con todos sus campos y detalles
    
    Args:
        activo: Filtro por estado activo (True, False, None para todos)
        limite: Número máximo de componentes a listar
        filtro: Filtro de búsqueda por nombre o código
    
    Returns:
        dict: Lista de componentes con todos sus campos
    """
    try:
        from django.db import connection
        connection.ensure_connection()
        componentes = Componente.objects.all()
        
        if activo is not None:
            componentes = componentes.filter(activo=activo)
        
        if filtro:
            componentes = componentes.filter(
                Q(nombre__icontains=filtro) | Q(codigo__icontains=filtro)
            )
        
        componentes = componentes.order_by('nombre')[:limite]
        
        lista_componentes = []
        for c in componentes:
            try:
                hijos_count = c.hijos.count() if hasattr(c, 'hijos') else 0
                
                componente_data = {
                    "id": c.id,
                    "nombre": c.nombre or "N/A",
                    "codigo": c.codigo or "N/A",
                    "activo": c.activo,
                    "padre": c.padre.nombre if c.padre else None,
                    "padre_codigo": c.padre.codigo if c.padre else None,
                    "hijos_count": hijos_count
                }
                lista_componentes.append(componente_data)
            except Exception as e_comp:
                logger.warning(f"Error procesando componente {c.id if hasattr(c, 'id') else 'N/A'}: {str(e_comp)}")
                continue
        
        return {
            "total_encontrados": len(lista_componentes),
            "filtro_activo": activo,
            "componentes": lista_componentes
        }
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error en listado_componentes_data: {error_type}: {error_msg}", exc_info=True)
        return {
            "error": f"Error al listar componentes: {error_msg}",
            "error_type": error_type,
            "success": False
        }


def listado_acciones_data(limite=100, filtro=None):
    """
    Lista todas las acciones disponibles en el sistema
    
    Args:
        limite: Número máximo de acciones a listar
        filtro: Filtro de búsqueda por nombre
    
    Returns:
        dict: Lista de acciones con todos sus campos
    """
    try:
        from django.db import connection
        connection.ensure_connection()
        acciones = Accion.objects.all()
        
        if filtro:
            acciones = acciones.filter(nombre__icontains=filtro)
        
        acciones = acciones.order_by('nombre')[:limite]
        
        lista_acciones = []
        for a in acciones:
            try:
                # Contar cuántas veces se usa esta acción
                uso_count = ComponenteAccion.objects.filter(accion=a).count()
                
                accion_data = {
                    "id": a.id,
                    "nombre": a.nombre or "N/A",
                    "uso_count": uso_count
                }
                lista_acciones.append(accion_data)
            except Exception as e_acc:
                logger.warning(f"Error procesando acción {a.id if hasattr(a, 'id') else 'N/A'}: {str(e_acc)}")
                continue
        
        return {
            "total_encontrados": len(lista_acciones),
            "acciones": lista_acciones
        }
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error en listado_acciones_data: {error_type}: {error_msg}", exc_info=True)
        return {
            "error": f"Error al listar acciones: {error_msg}",
            "error_type": error_type,
            "success": False
        }


def listado_diagnosticos_data(estado=None, limite=50, filtro=None):
    """
    Lista todos los diagnósticos del sistema con todos sus campos y detalles
    
    Args:
        estado: Filtro por estado (pendiente, aprobado, rechazado, None para todos)
        limite: Número máximo de diagnósticos a listar
        filtro: Filtro de búsqueda por placa del vehículo
    
    Returns:
        dict: Lista de diagnósticos con todos sus campos
    """
    try:
        from django.db import connection
        connection.ensure_connection()
        diagnosticos = Diagnostico.objects.filter(visible=True)
        
        if estado:
            diagnosticos = diagnosticos.filter(estado=estado)
        
        if filtro:
            diagnosticos = diagnosticos.filter(
                Q(vehiculo__placa__icontains=filtro) |
                Q(vehiculo__marca__icontains=filtro) |
                Q(vehiculo__modelo__icontains=filtro)
            )
        
        diagnosticos = diagnosticos.order_by('-fecha')[:limite]
        
        lista_diagnosticos = []
        for d in diagnosticos:
            try:
                vehiculo = d.vehiculo
                acciones_count = d.acciones_componentes.count() if hasattr(d, 'acciones_componentes') else 0
                repuestos_count = d.repuestos.count() if hasattr(d, 'repuestos') else 0
                
                diagnostico_data = {
                    "id": d.id,
                    "vehiculo": {
                        "placa": vehiculo.placa if vehiculo else "N/A",
                        "marca": vehiculo.marca if vehiculo else "N/A",
                        "modelo": vehiculo.modelo if vehiculo else "N/A",
                        "anio": vehiculo.anio if vehiculo else "N/A"
                    },
                    "cliente": {
                        "rut": vehiculo.cliente.rut if vehiculo and vehiculo.cliente else "N/A",
                        "nombre": vehiculo.cliente.nombre if vehiculo and vehiculo.cliente else "N/A"
                    },
                    "descripcion_problema": d.descripcion_problema or "",
                    "fecha": d.fecha.strftime("%Y-%m-%d %H:%M:%S") if d.fecha else None,
                    "estado": d.estado,
                    "estado_display": d.get_estado_display() if hasattr(d, 'get_estado_display') else str(d.estado),
                    "total_mano_obra": float(d.total_mano_obra) if hasattr(d, 'total_mano_obra') else 0.0,
                    "total_repuestos": float(d.total_repuestos) if hasattr(d, 'total_repuestos') else 0.0,
                    "total_presupuesto": float(d.total_presupuesto) if hasattr(d, 'total_presupuesto') else 0.0,
                    "acciones_count": acciones_count,
                    "repuestos_count": repuestos_count
                }
                lista_diagnosticos.append(diagnostico_data)
            except Exception as e_diag:
                logger.warning(f"Error procesando diagnóstico {d.id if hasattr(d, 'id') else 'N/A'}: {str(e_diag)}")
                continue
        
        return {
            "total_encontrados": len(lista_diagnosticos),
            "estado_filtro": estado,
            "diagnosticos": lista_diagnosticos
        }
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error en listado_diagnosticos_data: {error_type}: {error_msg}", exc_info=True)
        return {
            "error": f"Error al listar diagnósticos: {error_msg}",
            "error_type": error_type,
            "success": False
        }


def listado_compatibilidad_data(repuesto_id=None, vehiculo_id=None, limite=50):
    """
    Lista información de compatibilidad entre repuestos y vehículos
    
    Args:
        repuesto_id: ID del repuesto para buscar vehículos compatibles
        vehiculo_id: ID del vehículo para buscar repuestos compatibles
        limite: Número máximo de resultados a listar
    
    Returns:
        dict: Lista de compatibilidades
    """
    try:
        from django.db import connection
        connection.ensure_connection()
        
        if repuesto_id:
            # Buscar vehículos compatibles para un repuesto
            try:
                repuesto = Repuesto.objects.get(id=repuesto_id)
                aplicaciones = RepuestoAplicacion.objects.filter(repuesto=repuesto)[:limite]
                
                compatibilidades = []
                for app in aplicaciones:
                    compatibilidades.append({
                        "repuesto": {
                            "id": repuesto.id,
                            "nombre": repuesto.nombre,
                            "sku": repuesto.sku or "N/A"
                        },
                        "vehiculo": {
                            "marca": app.version.marca,
                            "modelo": app.version.modelo,
                            "anio_desde": app.version.anio_desde,
                            "anio_hasta": app.version.anio_hasta,
                            "motor": app.motor or app.version.motor or "N/A",
                            "carroceria": app.carroceria or app.version.carroceria or "N/A"
                        },
                        "posicion": app.posicion or "N/A"
                    })
                
                return {
                    "total_encontrados": len(compatibilidades),
                    "tipo": "repuesto_a_vehiculos",
                    "compatibilidades": compatibilidades
                }
            except Repuesto.DoesNotExist:
                return {"error": f"Repuesto con ID {repuesto_id} no encontrado", "success": False}
        
        elif vehiculo_id:
            # Buscar repuestos compatibles para un vehículo
            try:
                vehiculo = Vehiculo.objects.get(id=vehiculo_id)
                # Buscar versiones que coincidan con el vehículo
                versiones = VehiculoVersion.objects.filter(
                    marca=vehiculo.marca,
                    modelo=vehiculo.modelo,
                    anio_desde__lte=vehiculo.anio,
                    anio_hasta__gte=vehiculo.anio
                )[:limite]
                
                compatibilidades = []
                for version in versiones:
                    aplicaciones = RepuestoAplicacion.objects.filter(version=version)[:10]
                    for app in aplicaciones:
                        compatibilidades.append({
                            "repuesto": {
                                "id": app.repuesto.id,
                                "nombre": app.repuesto.nombre,
                                "sku": app.repuesto.sku or "N/A"
                            },
                            "vehiculo": {
                                "marca": version.marca,
                                "modelo": version.modelo,
                                "anio_desde": version.anio_desde,
                                "anio_hasta": version.anio_hasta
                            }
                        })
                
                return {
                    "total_encontrados": len(compatibilidades),
                    "tipo": "vehiculo_a_repuestos",
                    "compatibilidades": compatibilidades
                }
            except Vehiculo.DoesNotExist:
                return {"error": f"Vehículo con ID {vehiculo_id} no encontrado", "success": False}
        
        else:
            # Listar todas las compatibilidades
            aplicaciones = RepuestoAplicacion.objects.all()[:limite]
            compatibilidades = []
            for app in aplicaciones:
                compatibilidades.append({
                    "repuesto": {
                        "id": app.repuesto.id,
                        "nombre": app.repuesto.nombre
                    },
                    "vehiculo": {
                        "marca": app.version.marca,
                        "modelo": app.version.modelo,
                        "anio_desde": app.version.anio_desde,
                        "anio_hasta": app.version.anio_hasta
                    }
                })
            
            return {
                "total_encontrados": len(compatibilidades),
                "tipo": "todas",
                "compatibilidades": compatibilidades
            }
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error en listado_compatibilidad_data: {error_type}: {error_msg}", exc_info=True)
        return {
            "error": f"Error al listar compatibilidades: {error_msg}",
            "error_type": error_type,
            "success": False
        }


def listado_compras_data(estado=None, limite=50, filtro=None):
    """
    Lista todas las compras del sistema con todos sus campos y detalles
    
    Args:
        estado: Filtro por estado (borrador, confirmada, recibida, cancelada, None para todos)
        limite: Número máximo de compras a listar
        filtro: Filtro de búsqueda por número de compra o proveedor
    
    Returns:
        dict: Lista de compras con todos sus campos
    """
    try:
        from django.db import connection
        connection.ensure_connection()
        compras = Compra.objects.all()
        
        if estado:
            compras = compras.filter(estado=estado)
        
        if filtro:
            compras = compras.filter(
                Q(numero_compra__icontains=filtro) | Q(proveedor__icontains=filtro)
            )
        
        compras = compras.order_by('-fecha_compra', '-creado_en')[:limite]
        
        lista_compras = []
        for c in compras:
            try:
                items_count = c.items.count() if hasattr(c, 'items') else 0
                
                compra_data = {
                    "id": c.id,
                    "numero_compra": c.numero_compra or "N/A",
                    "proveedor": c.proveedor or "N/A",
                    "fecha_compra": c.fecha_compra.strftime("%Y-%m-%d") if c.fecha_compra else None,
                    "fecha_recibida": c.fecha_recibida.strftime("%Y-%m-%d") if c.fecha_recibida else None,
                    "estado": c.estado,
                    "estado_display": c.get_estado_display() if hasattr(c, 'get_estado_display') else str(c.estado),
                    "total": float(c.total) if c.total else 0.0,
                    "observaciones": c.observaciones or "",
                    "items_count": items_count,
                    "creado_en": c.creado_en.strftime("%Y-%m-%d %H:%M:%S") if c.creado_en else None
                }
                lista_compras.append(compra_data)
            except Exception as e_compra:
                logger.warning(f"Error procesando compra {c.id if hasattr(c, 'id') else 'N/A'}: {str(e_compra)}")
                continue
        
        return {
            "total_encontrados": len(lista_compras),
            "estado_filtro": estado,
            "compras": lista_compras
        }
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error en listado_compras_data: {error_type}: {error_msg}", exc_info=True)
        return {
            "error": f"Error al listar compras: {error_msg}",
            "error_type": error_type,
            "success": False
        }


def listado_inventario_data(limite=200, filtro=None, stock_minimo=None):
    """
    Lista el inventario de repuestos con información de stock
    
    Args:
        limite: Número máximo de repuestos a listar (default: 200 para cubrir todos los registros)
        filtro: Filtro de búsqueda por nombre, SKU, código o marca
        stock_minimo: Filtrar solo repuestos con stock menor o igual a este valor
    
    Returns:
        dict: Lista de repuestos con información de inventario
    """
    try:
        from django.db import connection
        connection.ensure_connection()
        repuestos = Repuesto.objects.all()
        
        if filtro:
            # Búsqueda más amplia: nombre, SKU, código de barras, marca, referencia, descripción
            repuestos = repuestos.filter(
                Q(nombre__icontains=filtro) | 
                Q(sku__icontains=filtro) | 
                Q(codigo_barra__icontains=filtro) |
                Q(marca__icontains=filtro) |
                Q(referencia__icontains=filtro) |
                Q(descripcion__icontains=filtro)
            )
        
        # Obtener el total REAL de registros ANTES de aplicar límite
        total_real_registros = repuestos.count()
        
        # Asegurar que el límite cubra TODOS los registros si no hay filtro
        if not filtro:
            # Usar el total real + margen para asegurar que se procesen todos
            limite = max(limite, total_real_registros + 100)  # +100 para margen de seguridad
        elif limite < 200:
            limite = 200
        
        # Ordenar correctamente: primero por nombre, luego por id como desempate
        repuestos_ordenados = repuestos.order_by('nombre', 'id')[:limite]
        
        # Forzar evaluación del queryset ANTES de convertirlo a lista
        # Usar iterator() para procesar en lotes y evitar problemas de memoria
        repuestos_lista = list(repuestos_ordenados)
        
        logger.info(f"listado_inventario_data: total_real={total_real_registros}, limite={limite}, repuestos_en_lista={len(repuestos_lista)}")
        
        lista_inventario = []
        errores_procesamiento = 0
        procesados = 0
        
        # Optimizar: Pre-cargar todos los stocks de una vez usando prefetch_related
        from django.db.models import Sum, Q as Q_stock
        repuestos_con_stock = RepuestoEnStock.objects.values('repuesto').annotate(
            stock_total=Sum('stock'),
            stock_reservado=Sum('reservado')
        )
        
        # Crear un diccionario para acceso rápido: {repuesto_id: {stock_total, stock_reservado}}
        stock_dict = {}
        for item in repuestos_con_stock:
            rep_id = item['repuesto']
            stock_dict[rep_id] = {
                'total': item['stock_total'] or 0,
                'reservado': item['stock_reservado'] or 0,
                'disponible': (item['stock_total'] or 0) - (item['stock_reservado'] or 0)
            }
        
        # Procesar TODOS los repuestos de la lista de forma optimizada
        for r in repuestos_lista:
            procesados += 1
            try:
                # Obtener stock del diccionario pre-calculado (mucho más rápido)
                stock_info = stock_dict.get(r.id, {'total': 0, 'reservado': 0, 'disponible': 0})
                stock_total = stock_info['total']
                stock_reservado = stock_info['reservado']
                stock_disponible = stock_info['disponible']
                
                # Si se especifica stock_minimo Y hay un filtro de búsqueda, aplicar filtro de stock
                # Si NO hay filtro de búsqueda, mostrar TODOS los repuestos sin filtrar por stock
                # (porque el usuario pidió "todos los registros")
                if stock_minimo is not None and filtro:
                    if stock_total > stock_minimo:
                        continue  # Saltar este repuesto si tiene más stock que el mínimo especificado
                # Si no hay filtro de búsqueda, agregar TODOS los repuestos sin importar el stock
                
                # Agregar TODOS los repuestos que pasen el filtro (o todos si no hay filtro)
                inventario_data = {
                    "id": r.id,
                    "nombre": r.nombre or "N/A",
                    "sku": r.sku or "N/A",
                    "codigo_barra": r.codigo_barra or "N/A",
                    "marca": r.marca or "N/A",
                    "precio_costo": float(r.precio_costo) if r.precio_costo else 0.0,
                    "precio_venta": float(r.precio_venta) if r.precio_venta else 0.0,
                    "stock": {
                        "total": stock_total,
                        "reservado": stock_reservado,
                        "disponible": stock_disponible
                    },
                    "unidad": r.unidad or "pieza"
                }
                lista_inventario.append(inventario_data)
            except Exception as e_inv:
                errores_procesamiento += 1
                logger.warning(f"Error procesando inventario para repuesto {r.id if hasattr(r, 'id') else 'N/A'}: {str(e_inv)}", exc_info=True)
                # Agregar información básica incluso si hay error
                try:
                    inventario_data = {
                        "id": r.id,
                        "nombre": r.nombre or "N/A",
                        "sku": r.sku or "N/A",
                        "codigo_barra": r.codigo_barra or "N/A",
                        "marca": r.marca or "N/A",
                        "precio_costo": float(r.precio_costo) if r.precio_costo else 0.0,
                        "precio_venta": float(r.precio_venta) if r.precio_venta else 0.0,
                        "stock": {
                            "total": 0,
                            "reservado": 0,
                            "disponible": 0
                        },
                        "unidad": r.unidad or "pieza",
                        "error_stock": "Error al obtener stock"
                    }
                    lista_inventario.append(inventario_data)
                except Exception as e2:
                    logger.error(f"Error crítico procesando repuesto {r.id if hasattr(r, 'id') else 'N/A'}: {str(e2)}", exc_info=True)
                    continue
        
        logger.info(f"listado_inventario_data: procesados={procesados}, agregados={len(lista_inventario)}, errores={errores_procesamiento}, stock_minimo={stock_minimo}")
        
        # Si no se agregaron todos los registros esperados y no hay filtro, hay un problema
        if len(lista_inventario) < total_real_registros and not filtro and stock_minimo is None:
            logger.warning(f"ADVERTENCIA: Se procesaron {procesados} repuestos pero solo se agregaron {len(lista_inventario)}. Esperados: {total_real_registros}")
        
        return {
            "total_real_registros": total_real_registros,  # Total real en la tabla
            "total_encontrados": len(lista_inventario),  # Total procesados exitosamente
            "total_procesados": procesados,  # Total de repuestos procesados en el loop
            "errores_procesamiento": errores_procesamiento,
            "inventario": lista_inventario
        }
    
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error en listado_inventario_data: {error_type}: {error_msg}", exc_info=True)
        return {
            "error": f"Error al listar inventario: {error_msg}",
            "error_type": error_type,
            "success": False
        }


def test_function_call_data():
    """
    Función de test muy simple para diagnosticar problemas con function_calls.
    No accede a la base de datos ni hace operaciones complejas.
    Solo devuelve un mensaje fijo para verificar que las function_calls funcionan.
    """
    try:
        import datetime
        return {
            "success": True,
            "message": "Función de test ejecutada correctamente",
            "timestamp": datetime.datetime.now().isoformat(),
            "test_data": {
                "status": "ok",
                "function": "test_function_call",
                "description": "Esta es una función de test simple para diagnosticar problemas"
            }
        }
    except Exception as e:
        return {"error": f"Error en función de test: {str(e)}"}


def test2_function_call_data():
    """
    Función de test para diagnosticar problemas de conexión a la base de datos.
    Se conecta directamente a la tabla Mecanico y lista solo los nombres.
    Genera logs detallados en un archivo para análisis.
    """
    import os
    import datetime
    from pathlib import Path
    from django.db import connection
    from django.conf import settings
    
    # Determinar ruta del archivo de log (siempre convertir a string)
    if isinstance(settings.BASE_DIR, Path):
        log_file_path = str(settings.BASE_DIR / 'test2_db_log.txt')
    else:
        log_file_path = str(os.path.join(settings.BASE_DIR, 'test2_db_log.txt'))
    log_entries = []
    
    def log_entry(message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        log_entries.append(log_msg)
        logger.info(log_msg)
    
    try:
        log_entry("=== INICIO test2_function_call_data ===")
        
        # Verificar conexión
        log_entry("Verificando conexión a la base de datos...")
        connection.ensure_connection()
        log_entry(f"Conexión establecida. Base de datos: {connection.settings_dict.get('NAME', 'N/A')}")
        
        # Intentar consulta simple
        log_entry("Intentando consulta: Mecanico.objects.all()")
        mecanicos = Mecanico.objects.all()
        log_entry(f"Query ejecutado. Tipo: {type(mecanicos)}")
        
        # Contar resultados
        log_entry("Contando resultados...")
        count = mecanicos.count()
        log_entry(f"Total de mecánicos encontrados: {count}")
        
        # Obtener nombres
        log_entry("Obteniendo nombres de mecánicos...")
        nombres = []
        for i, mecanico in enumerate(mecanicos[:50]):  # Limitar a 50 para no sobrecargar
            try:
                # Intentar obtener el nombre del usuario asociado
                if hasattr(mecanico, 'user') and mecanico.user:
                    nombre = mecanico.user.get_full_name() or mecanico.user.username
                else:
                    nombre = f"Mecanico-{mecanico.id}"
                
                nombres.append({
                    "id": mecanico.id,
                    "nombre": nombre,
                    "activo": getattr(mecanico, 'activo', None)
                })
                log_entry(f"Mecánico {i+1}: ID={mecanico.id}, Nombre={nombre}")
            except Exception as e_mec:
                log_entry(f"Error procesando mecánico {i+1}: {str(e_mec)}")
                nombres.append({
                    "id": mecanico.id if hasattr(mecanico, 'id') else 'N/A',
                    "nombre": f"Error: {str(e_mec)}",
                    "activo": None
                })
        
        log_entry(f"Total de nombres obtenidos: {len(nombres)}")
        
        # Información de la conexión (asegurar que todos los valores sean strings)
        db_name = connection.settings_dict.get('NAME', 'N/A')
        if db_name and not isinstance(db_name, str):
            db_name = str(db_name)
        
        db_info = {
            "engine": str(connection.settings_dict.get('ENGINE', 'N/A')),
            "name": db_name,
            "host": str(connection.settings_dict.get('HOST', 'N/A')),
            "port": str(connection.settings_dict.get('PORT', 'N/A')) if connection.settings_dict.get('PORT') else 'N/A',
            "user": str(connection.settings_dict.get('USER', 'N/A')),
        }
        log_entry(f"Info BD: {db_info}")
        
        # Escribir log a archivo
        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write('\n'.join(log_entries))
                f.write('\n\n')
            log_entry(f"Log guardado en: {log_file_path}")
        except Exception as e_log:
            log_entry(f"Error escribiendo log a archivo: {str(e_log)}")
        
        return {
            "success": True,
            "message": "Función test2 ejecutada correctamente",
            "timestamp": datetime.datetime.now().isoformat(),
            "total_mecanicos": count,
            "nombres_obtenidos": len(nombres),
            "nombres": nombres,
            "db_info": db_info,
            "log_file": log_file_path,
            "log_entries_count": len(log_entries)
        }
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        log_entry(f"ERROR: {error_type}: {error_msg}")
        
        # Intentar escribir el error al log
        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write('\n'.join(log_entries))
                f.write(f'\nERROR FINAL: {error_type}: {error_msg}\n\n')
        except:
            pass
        
        logger.error(f"Error en test2_function_call_data: {error_type}: {error_msg}", exc_info=True)
        
        return {
            "error": f"Error en función test2: {error_msg}",
            "error_type": error_type,
            "success": False,
            "log_file": log_file_path,
            "log_entries": log_entries[-10:]  # Últimas 10 entradas del log
        }


@login_required
def netgogo_console(request):
    """Vista para renderizar la consola de IA Netgogo - Solo accesible para maxgonpe temporalmente"""
    # Restricción temporal: solo el usuario maxgonpe puede acceder
    if request.user.username != 'maxgonpe':
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "Acceso restringido. Esta funcionalidad está en desarrollo.")
        return redirect('panel_principal')
    
    return render(request, "car/netgogo_console.html")


@csrf_exempt
@ajax_login_required
def netgogo_chat(request):
    """Vista para manejar las peticiones del chat de Netgogo - Solo accesible para maxgonpe temporalmente"""
    try:
        # Restricción temporal: solo el usuario maxgonpe puede acceder
        if not request.user.is_authenticated:
            return JsonResponse({"error": "No autenticado. Por favor inicia sesión."}, status=401)
        
        if request.user.username != 'maxgonpe':
            return JsonResponse({"error": "Acceso restringido. Esta funcionalidad está en desarrollo."}, status=403)
        
        if request.method != 'POST':
            return JsonResponse({"error": "Método no permitido. Use POST."}, status=405)
        
        # Obtener datos del request
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando JSON en netgogo_chat: {str(e)}")
                return JsonResponse({"error": "JSON inválido"}, status=400)
        else:
            data = request.POST
        
        user_input = data.get("input", "").strip()
        reset_session = data.get("reset", False)
        
        if not user_input and not reset_session:
            return JsonResponse({"error": "Falta parámetro 'input'"}, status=400)
        
        # Validar comandos de salida
        if user_input.lower() in ("salir", "exit", "bye", "sayonara"):
            return JsonResponse({
                "message": "Hasta luego!",
                "reset": True
            })
        
        # Obtener o crear agente en la sesión
        if reset_session or 'netgogo_agent' not in request.session:
            agent = Agent()
            request.session['netgogo_agent'] = {
                'messages': agent.messages.copy()
            }
        else:
            agent = Agent()
            agent.messages = request.session['netgogo_agent']['messages'].copy()
        
        # Agregar mensaje del usuario al historial
        agent.messages.append({"role": "user", "content": user_input})
    
        # Importar función de conexión a la API desde views_api
        from .views_api import call_openai_api
        
        # Preparar mensajes para la API
        # La API espera mensajes en formato estándar: {role, content}
        # Limpiar y filtrar mensajes para formato compatible
        messages_for_api = []
        for msg in agent.messages:
            if isinstance(msg, dict):
                # Solo incluir mensajes con role y content (formato estándar)
                if 'role' in msg and 'content' in msg:
                    # Asegurar que content sea string
                    content = msg['content']
                    if not isinstance(content, str):
                        content = str(content)
                    
                    # Crear mensaje limpio solo con role y content
                    clean_msg = {
                        "role": msg['role'],
                        "content": content
                    }
                    messages_for_api.append(clean_msg)
                
                # Convertir function_call_output a formato de mensaje function
                elif msg.get('type') == 'function_call_output':
                    # Convertir output de función a formato compatible
                    output_content = msg.get('output', '')
                    if isinstance(output_content, str):
                        try:
                            # Intentar parsear JSON si es string JSON
                            output_content = json.loads(output_content)
                        except:
                            pass
                    
                    # Formato para mensaje de función
                    function_msg = {
                        "role": "function",
                        "name": "function_output",
                        "content": json.dumps(output_content) if not isinstance(output_content, str) else output_content
                    }
                    messages_for_api.append(function_msg)
        
        # Si no hay mensajes válidos, usar solo el último mensaje del usuario
        if not messages_for_api:
            messages_for_api = [{"role": "user", "content": user_input}]
        
        # Validar que todos los mensajes tengan el formato correcto
        validated_messages = []
        for msg in messages_for_api:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                # Asegurar que content sea string
                if not isinstance(msg['content'], str):
                    msg['content'] = str(msg['content'])
                validated_messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
            elif isinstance(msg, dict) and msg.get('role') == 'function':
                # Mensaje de función con name
                validated_messages.append({
                    "role": "function",
                    "name": msg.get('name', 'function_output'),
                    "content": str(msg.get('content', ''))
                })
        
        messages_for_api = validated_messages if validated_messages else [{"role": "user", "content": user_input}]
        
        # Construir el historial completo para mantener contexto
        # Intentar primero con lista de mensajes (formato estándar de chat)
        # Si la API no lo acepta, construiremos un string con el contexto
        input_for_api = messages_for_api  # Intentar con lista completa primero
        
        # Llamar a la API usando la función de conexión
        # ACTIVAR herramientas para que la IA pueda usar function_calls
        response_data = call_openai_api(
            input_data=input_for_api,  # Enviar historial completo como lista
            model="gpt-5-nano",
            tools=agent.tools,  # ACTIVADO: Herramientas disponibles
            store=True,
            timeout=60
        )
        
        # Procesar respuesta con el agente
        # ACTIVADO: Procesar herramientas si se llaman
        called_tool = False
        tool_info = None
        final_message = None
        
        # La respuesta viene en formato: {"output": [{"type": "message" o "function_call", ...}]}
        if 'output' in response_data:
            outputs = response_data.get('output', [])
            for output in outputs:
                if isinstance(output, dict):
                    output_type = output.get('type')
                    
                    # Si es function_call, ejecutarla
                    if output_type == 'function_call':
                        fn_name = output.get('name')
                        args_str = output.get('arguments', '{}')
                        
                        try:
                            args = json.loads(args_str) if isinstance(args_str, str) else args_str
                        except:
                            args = {}
                        
                        called_tool = True
                        tool_info = {
                            'name': fn_name,
                            'arguments': args,
                            'call_id': output.get('call_id', '')
                        }
                        
                        # Ejecutar la función correspondiente
                        try:
                            if fn_name == 'listado_trabajos':
                                estado = args.get('estado', 'todos')
                                limite = args.get('limite', 20)
                                result = listado_trabajos_data(estado=estado, limite=limite)
                            elif fn_name == 'listado_mecanicos':
                                activo = args.get('activo')
                                limite = args.get('limite', 50)
                                result = listado_mecanicos_data(activo=activo, limite=limite)
                            elif fn_name == 'query_sistema':
                                result = query_sistema_data(
                                    tipo=args.get('tipo'),
                                    filtro=args.get('filtro'),
                                    detalle=args.get('detalle', False)
                                )
                            elif fn_name == 'list_files_in_dir':
                                result = agent.list_files_in_dir(**args)
                            elif fn_name == 'read_file':
                                result = agent.read_file(**args)
                            elif fn_name == 'edit_file':
                                result = agent.edit_file(**args)
                            elif fn_name == 'test_function_call':
                                result = test_function_call_data()
                            elif fn_name == 'test2':
                                result = test2_function_call_data()
                            elif fn_name == 'netgogo':
                                result = agent.activate_netgogo_mode()
                            elif fn_name == 'listado_clientes':
                                activo = args.get('activo')
                                limite = args.get('limite', 50)
                                filtro = args.get('filtro')
                                result = listado_clientes_data(activo=activo, limite=limite, filtro=filtro)
                            elif fn_name == 'listado_vehiculos':
                                limite = args.get('limite', 50)
                                filtro = args.get('filtro')
                                result = listado_vehiculos_data(limite=limite, filtro=filtro)
                            elif fn_name == 'listado_componentes':
                                activo = args.get('activo')
                                limite = args.get('limite', 100)
                                filtro = args.get('filtro')
                                result = listado_componentes_data(activo=activo, limite=limite, filtro=filtro)
                            elif fn_name == 'listado_acciones':
                                limite = args.get('limite', 100)
                                filtro = args.get('filtro')
                                result = listado_acciones_data(limite=limite, filtro=filtro)
                            elif fn_name == 'listado_diagnosticos':
                                estado = args.get('estado')
                                limite = args.get('limite', 50)
                                filtro = args.get('filtro')
                                result = listado_diagnosticos_data(estado=estado, limite=limite, filtro=filtro)
                            elif fn_name == 'listado_compatibilidad':
                                repuesto_id = args.get('repuesto_id')
                                vehiculo_id = args.get('vehiculo_id')
                                limite = args.get('limite', 50)
                                result = listado_compatibilidad_data(repuesto_id=repuesto_id, vehiculo_id=vehiculo_id, limite=limite)
                            elif fn_name == 'listado_compras':
                                estado = args.get('estado')
                                limite = args.get('limite', 50)
                                filtro = args.get('filtro')
                                result = listado_compras_data(estado=estado, limite=limite, filtro=filtro)
                            elif fn_name == 'listado_inventario':
                                limite = args.get('limite', 200)
                                filtro = args.get('filtro')
                                stock_minimo = args.get('stock_minimo')
                                result = listado_inventario_data(limite=limite, filtro=filtro, stock_minimo=stock_minimo)
                            else:
                                result = {"error": f"Función desconocida: {fn_name}", "success": False}
                            
                            # Asegurar que result siempre sea un dict
                            if not isinstance(result, dict):
                                result = {"result": result, "success": True}
                                
                        except Exception as func_error:
                            error_msg = str(func_error)
                            error_type = type(func_error).__name__
                            logger.error(f"Error ejecutando función {fn_name}: {error_type}: {error_msg}", exc_info=True)
                            result = {
                                "error": f"Error ejecutando {fn_name}: {error_msg}",
                                "error_type": error_type,
                                "success": False
                            }
                        
                        tool_info['result'] = result
                        
                        # Agregar resultado al historial
                        agent.messages.append({
                            "type": "function_call_output",
                            "call_id": output.get('call_id', ''),
                            "output": json.dumps({
                                "result": result
                            })
                        })
                        
                        # Continuar conversación para obtener respuesta final
                        try:
                            continuation_messages = []
                            for msg in agent.messages:
                                if isinstance(msg, dict):
                                    if 'role' in msg and 'content' in msg:
                                        continuation_messages.append({
                                            "role": msg['role'],
                                            "content": str(msg['content'])
                                        })
                                    elif msg.get('type') == 'function_call_output':
                                        output_content = msg.get('output', '')
                                        continuation_messages.append({
                                            "role": "function",
                                            "name": "function_output",
                                            "content": output_content if isinstance(output_content, str) else json.dumps(output_content)
                                        })
                            
                            # Agregar mensaje explícito pidiendo que procese el resultado
                            continuation_messages.append({
                                "role": "user",
                                "content": (
                                    f"Procesa el resultado de la función '{fn_name}' que acabas de ejecutar. "
                                    f"Responde al usuario de forma clara y amigable, extrayendo la información relevante del resultado. "
                                    f"NO muestres el JSON crudo, sino presenta los datos de manera legible. "
                                    f"Si el usuario pidió información específica, extrae solo esos campos."
                                )
                            })
                            
                            continuation_response = call_openai_api(
                                input_data=continuation_messages,
                                model="gpt-5-nano",
                                tools=None,  # No necesitamos herramientas en la continuación
                                store=True,
                                timeout=60
                            )
                            
                            # Procesar respuesta de continuación
                            if 'output' in continuation_response:
                                cont_outputs = continuation_response.get('output', [])
                                for cont_output in cont_outputs:
                                    if isinstance(cont_output, dict) and cont_output.get('type') == 'message':
                                        content = cont_output.get('content', [])
                                        if isinstance(content, list):
                                            message_parts = []
                                            for part in content:
                                                if isinstance(part, dict) and part.get('type') == 'output_text':
                                                    text = part.get('text', '')
                                                    if text:
                                                        message_parts.append(text)
                                            final_message = '\n'.join(message_parts) if message_parts else None
                                        elif isinstance(content, str):
                                            final_message = content
                                        break
                            
                            # Si no se obtuvo mensaje de la continuación, crear uno básico desde el resultado
                            if not final_message:
                                # Intentar extraer información básica del resultado para crear un mensaje
                                if isinstance(result, dict) and 'error' not in result:
                                    try:
                                        if 'compras' in result:
                                            final_message = f"Se encontraron {result.get('total_encontrados', 0)} compras."
                                        elif 'clientes' in result:
                                            final_message = f"Se encontraron {result.get('total_encontrados', 0)} clientes."
                                        elif 'vehiculos' in result:
                                            final_message = f"Se encontraron {result.get('total_encontrados', 0)} vehículos."
                                        elif 'trabajos' in result:
                                            final_message = f"Se encontraron {result.get('total_encontrados', 0)} trabajos."
                                        elif 'mecanicos' in result:
                                            final_message = f"Se encontraron {result.get('total_encontrados', 0)} mecánicos."
                                        else:
                                            final_message = "Datos obtenidos correctamente."
                                    except:
                                        final_message = "Datos obtenidos correctamente."
                                else:
                                    final_message = "Datos obtenidos correctamente."
                            
                            # Agregar respuesta al historial
                            if final_message:
                                agent.messages.append({
                                    "role": "assistant",
                                    "content": final_message
                                })
                            
                            # IMPORTANTE: Guardar el final_message para usarlo en la respuesta
                            tool_info['final_message'] = final_message
                            
                        except Exception as e:
                            print(f"Error en continuación después de {fn_name}: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            final_message = f"Datos obtenidos. {json.dumps(result, indent=2, ensure_ascii=False)[:500]}..."
                            tool_info['final_message'] = final_message
                    
                    # Si es message, extraer el texto
                    elif output_type == 'message':
                        content = output.get('content', [])
                        if isinstance(content, list):
                            message_parts = []
                            for part in content:
                                if isinstance(part, dict) and part.get('type') == 'output_text':
                                    text = part.get('text', '')
                                    if text:
                                        message_parts.append(text)
                                elif isinstance(part, str):
                                    message_parts.append(part)
                            final_message = '\n'.join(message_parts) if message_parts else None
                        elif isinstance(content, str):
                            final_message = content
            
            # Si no se encontró mensaje, intentar usar el campo 'text' de la respuesta
            if not final_message and 'text' in response_data:
                final_message = response_data['text']
            
            # Agregar la respuesta del asistente al historial para mantener contexto (si no se llamó herramienta)
            if final_message and not called_tool:
                agent.messages.append({
                    "role": "assistant",
                    "content": final_message
                })
        
        # Si la respuesta NO tiene 'output', es una respuesta directa de la IA
        elif 'message' in response_data:
            final_message = response_data['message']
        elif 'content' in response_data:
            final_message = response_data['content']
        else:
            # Intentar extraer mensaje de la estructura
            final_message = str(response_data) if response_data else "No se recibió respuesta"
        
        # Guardar estado del agente en sesión (SIEMPRE actualizar con el historial completo)
        request.session['netgogo_agent'] = {
            'messages': agent.messages.copy()
        }
        request.session.modified = True
        
        # Preparar respuesta
        result = {
            "success": True,
            "message": final_message or "Procesado correctamente",
            "tool_called": called_tool,
        }
        
        if called_tool and tool_info:
            result["tool"] = {
                "name": tool_info.get('name'),
                "arguments": tool_info.get('arguments'),
                "result": tool_info.get('result')
            }
            
            # Mensajes específicos según la herramienta
            tool_name = tool_info.get('name')
            
            # Si hay un final_message de la continuación, usarlo como mensaje principal
            if tool_info.get('final_message'):
                result["message"] = tool_info.get('final_message')
            elif tool_name == 'listado_trabajos':
                result["message"] = f"📋 Listando trabajos del taller..."
            elif tool_name == 'listado_mecanicos':
                result["message"] = f"👷 Listando mecánicos del taller..."
            elif tool_name == 'query_sistema':
                result["message"] = f"📊 Consultando información del sistema: {tool_info.get('arguments', {}).get('tipo', 'desconocido')}..."
            elif tool_name == 'test_function_call':
                result["message"] = f"🧪 Función de test ejecutada correctamente. Verificando respuesta..."
            elif tool_name == 'test2':
                result["message"] = f"🔍 Test2 ejecutado. Revisando conexión a base de datos..."
            elif tool_name == 'netgogo':
                # El mensaje ya viene completo en result, solo asegurar que no necesita continuación
                pass
            elif tool_name == 'listado_clientes':
                result["message"] = f"👥 Listando clientes del taller..."
            elif tool_name == 'listado_vehiculos':
                result["message"] = f"🚗 Listando vehículos del taller..."
            elif tool_name == 'listado_componentes':
                result["message"] = f"🔧 Listando componentes del sistema..."
            elif tool_name == 'listado_acciones':
                result["message"] = f"⚙️ Listando acciones disponibles..."
            elif tool_name == 'listado_diagnosticos':
                result["message"] = f"📋 Listando diagnósticos (historial)..."
            elif tool_name == 'listado_compatibilidad':
                result["message"] = f"🔗 Consultando compatibilidad repuestos-vehículos..."
            elif tool_name == 'listado_compras':
                result["message"] = f"🛒 Listando compras del taller..."
            elif tool_name == 'listado_inventario':
                result["message"] = f"📦 Consultando inventario de repuestos..."
            else:
                result["message"] = f"⚙️ Herramienta '{tool_name}' ejecutada. Continuando..."
            
            result["needs_continuation"] = False  # Ya se procesó la continuación arriba
        else:
            result["needs_continuation"] = False
        
        return JsonResponse(result)
        
    except Exception as e:
        # Log detallado del error
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error(f"Error en netgogo_chat: {error_type}: {error_msg}", exc_info=True)
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Traceback completo: {error_trace}")
        
        # Verificar si es un error de base de datos
        is_db_error = any(db_error in error_type.lower() for db_error in [
            'database', 'connection', 'operational', 'integrity', 'doesnotexist'
        ]) or 'database' in error_msg.lower() or 'connection' in error_msg.lower()
        
        # Siempre devolver JSON, nunca HTML
        error_response = {
            "error": f"Error interno del servidor: {error_msg}",
            "error_type": error_type,
            "is_db_error": is_db_error,
            "success": False
        }
        
        if settings.DEBUG:
            error_response["details"] = error_trace
        
        return JsonResponse(error_response, status=500)






