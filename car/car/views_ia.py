from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count, Sum
import requests
import json
from .agent import Agent
from .models import Trabajo, Cliente_Taller, Vehiculo, Repuesto, Diagnostico, TrabajoAccion, TrabajoRepuesto, TrabajoAbono


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
            repuestos = Repuesto.objects.all()
            
            if filtro:
                repuestos = repuestos.filter(
                    Q(nombre__icontains=filtro) | Q(codigo__icontains=filtro) | Q(sku__icontains=filtro)
                )
            
            repuestos = repuestos.order_by('nombre')[:20]
            
            if detalle:
                datos = []
                for r in repuestos:
                    stock_total = r.stock_actual if hasattr(r, 'stock_actual') else 0
                    datos.append({
                        "id": r.id,
                        "nombre": r.nombre,
                        "codigo": r.codigo or "N/A",
                        "sku": r.sku or "N/A",
                        "precio_venta": float(r.precio_venta) if r.precio_venta else 0,
                        "stock": stock_total
                    })
            else:
                datos = {
                    "total": repuestos.count(),
                    "lista": [{"nombre": r.nombre, "codigo": r.codigo or "N/A", "precio": float(r.precio_venta) if r.precio_venta else 0} for r in repuestos[:10]]
                }
            
            return {"tipo": "repuesto", "datos": datos}
        
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
            return {"error": f"Error al consultar sistema: {str(e)}"}


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
            # Obtener información del vehículo
            vehiculo = t.vehiculo
            cliente = vehiculo.cliente
            
            # Obtener mecánicos asignados
            mecanicos = [{"id": m.id, "nombre": str(m)} for m in t.mecanicos.all()]
            
            # Obtener acciones del trabajo
            acciones = []
            for accion in t.acciones.all():
                acciones.append({
                    "id": accion.id,
                    "componente": accion.componente.nombre if accion.componente else "N/A",
                    "accion": accion.accion.nombre if accion.accion else "N/A",
                    "cantidad": float(accion.cantidad),
                    "precio_unitario": float(accion.precio_mano_obra),
                    "subtotal": float(accion.subtotal),
                    "completado": accion.completado
                })
            
            # Obtener repuestos del trabajo
            repuestos = []
            for repuesto in t.repuestos.all():
                repuestos.append({
                    "id": repuesto.id,
                    "repuesto": repuesto.repuesto.nombre if repuesto.repuesto else "N/A",
                    "cantidad": float(repuesto.cantidad),
                    "precio_unitario": float(repuesto.precio_unitario or 0),
                    "subtotal": float(repuesto.subtotal or 0),
                    "completado": repuesto.completado
                })
            
            # Obtener abonos
            abonos = []
            for abono in t.abonos.all():
                abonos.append({
                    "id": abono.id,
                    "fecha": abono.fecha.strftime("%Y-%m-%d") if abono.fecha else None,
                    "monto": float(abono.monto),
                    "observaciones": abono.observaciones or ""
                })
            
            trabajo_data = {
                "id": t.id,
                "vehiculo": {
                    "placa": vehiculo.placa,
                    "marca": vehiculo.marca,
                    "modelo": vehiculo.modelo,
                    "anio": vehiculo.anio,
                    "vin": vehiculo.vin or "N/A",
                    "descripcion_motor": vehiculo.descripcion_motor or "N/A"
                },
                "cliente": {
                    "rut": cliente.rut,
                    "nombre": cliente.nombre,
                    "telefono": cliente.telefono or "N/A",
                    "email": cliente.email or "N/A"
                },
                "fecha_inicio": t.fecha_inicio.strftime("%Y-%m-%d %H:%M:%S") if t.fecha_inicio else None,
                "fecha_fin": t.fecha_fin.strftime("%Y-%m-%d %H:%M:%S") if t.fecha_fin else None,
                "estado": t.estado,
                "estado_display": t.get_estado_display(),
                "observaciones": t.observaciones or "",
                "kilometraje_actual": t.lectura_kilometraje_actual,
                "mecanicos": mecanicos,
                "totales": {
                    "total_mano_obra": float(t.total_mano_obra),
                    "total_repuestos": float(t.total_repuestos),
                    "total_adicionales": float(t.total_adicionales),
                    "total_descuentos": float(t.total_descuentos),
                    "total_presupuestado": float(t.total_general),
                    "total_realizado_mano_obra": float(t.total_realizado_mano_obra),
                    "total_realizado_repuestos": float(t.total_realizado_repuestos),
                    "total_realizado": float(t.total_realizado),
                    "total_abonos": float(t.total_abonos),
                    "saldo_pendiente": float(t.total_general - t.total_abonos)
                },
                "acciones": acciones,
                "repuestos": repuestos,
                "abonos": abonos,
                "cantidad_acciones": len(acciones),
                "cantidad_repuestos": len(repuestos),
                "cantidad_abonos": len(abonos)
            }
            
            lista_trabajos.append(trabajo_data)
        
        return {
            "total_encontrados": len(lista_trabajos),
            "estado_filtro": estado,
            "trabajos": lista_trabajos
        }
    
    except Exception as e:
        return {"error": f"Error al listar trabajos: {str(e)}"}


@login_required
def netgogo_console(request):
    """Vista para renderizar la consola de IA Netgogo"""
    return render(request, "car/netgogo_console.html")


@csrf_exempt
@login_required
def netgogo_chat(request):
    """Vista para manejar las peticiones del chat de Netgogo"""
    if request.method != 'POST':
        return JsonResponse({"error": "Método no permitido. Use POST."}, status=405)
    
    # Obtener datos del request
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON inválido"}, status=400)
    else:
        data = request.POST
    
    user_input = data.get("input", "").strip()
    reset_session = data.get("reset", False)
    
    if not user_input:
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
    try:
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
                        if fn_name == 'listado_trabajos':
                            estado = args.get('estado', 'todos')
                            limite = args.get('limite', 20)
                            result = listado_trabajos_data(estado=estado, limite=limite)
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
                        else:
                            result = {"error": f"Función desconocida: {fn_name}"}
                        
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
                            
                            continuation_response = call_openai_api(
                                input_data=continuation_messages,
                                model="gpt-5-nano",
                                tools=agent.tools,
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
                            
                            # Agregar respuesta al historial
                            if final_message:
                                agent.messages.append({
                                    "role": "assistant",
                                    "content": final_message
                                })
                            
                        except Exception as e:
                            print(f"Error en continuación después de {fn_name}: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            final_message = f"Datos obtenidos. {json.dumps(result, indent=2, ensure_ascii=False)[:500]}..."
                    
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
            if tool_name == 'listado_trabajos':
                result["message"] = f"📋 Listando trabajos del taller..."
                result["needs_continuation"] = False  # Ya se procesó la continuación arriba
            elif tool_name == 'query_sistema':
                result["message"] = f"📊 Consultando información del sistema: {tool_info.get('arguments', {}).get('tipo', 'desconocido')}..."
                result["needs_continuation"] = False  # Ya se procesó la continuación arriba
            else:
                result["message"] = f"⚙️ Herramienta '{tool_name}' ejecutada. Continuando..."
                result["needs_continuation"] = False  # Ya se procesó la continuación arriba
        else:
            result["needs_continuation"] = False
        
        return JsonResponse(result)
    
    except Exception as e:
        print("Error en netgogo_chat:", str(e))
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": f"Error: {str(e)}"}, status=500)




