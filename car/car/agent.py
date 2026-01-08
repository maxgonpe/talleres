import os
import json
from pathlib import Path

class Agent:
    def __init__(self):
        self.setup_tools()
        self.messages = [
            {"role": "system", "content": (
                "Eres un asistente útil que habla español. "
                "IMPORTANTE: Cuando ejecutes una función y recibas su resultado, SIEMPRE debes procesar "
                "ese resultado y responder al usuario de forma clara y amigable, NO solo mostrar el JSON crudo. "
                "Extrae la información relevante del resultado y preséntala de manera legible. "
                "Si el usuario pide información específica (como 'solo el nombre y teléfono'), extrae solo esos campos. "
                "Sé conciso pero completo en tus respuestas."
            )}
        ]
    
    def setup_tools(self):
        self.tools = [
            {
                "type": "function",
                "name": "list_files_in_dir",
                "description": "Lista los archivos que existen en un directorio dado (por defecto es el directorio actual)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directorio para listar (opcional). Por defecto es el directorio actual"
                        }
                    },
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "read_file",
                "description": "Lee el contenido de un archivo en una ruta especificada",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "La ruta del archivo a leer"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "type": "function",
                "name": "edit_file",
                "description": "Edita el contenido de un archivo reemplazando prev_text por new_text. Crea el archivo si no existe.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "La ruta del archivo a editar"
                        },
                        "prev_text": {
                            "type": "string",
                            "description": "El texto que se va a buscar para reemplazar (puede ser vacío para archivos nuevos)"
                        },
                        "new_text": {
                            "type": "string",
                            "description": "El texto que reemplazará a prev_text (o el texto para un archivo nuevo)"
                        }
                    },
                    "required": ["path", "new_text"]
                }
            },
            {
                "type": "function",
                "name": "query_sistema",
                "description": "Consulta información del sistema del taller mecánico: trabajos, clientes, vehículos, repuestos y estadísticas. Úsala ESPECIALMENTE cuando el usuario pregunte por el NÚMERO TOTAL de registros en una tabla (ej: 'cuántos registros tiene la tabla repuestos', 'dame el total de registros de la tabla X', 'cuántos repuestos hay en total'). También úsala para consultas generales sobre el estado del taller, trabajos activos, clientes, vehículos o para contar registros de tablas específicas. IMPORTANTE: Para contar registros de tablas, usa esta función con tipo='repuesto', tipo='trabajo', etc. y sin filtro.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tipo": {
                            "type": "string",
                            "enum": ["trabajo", "cliente", "vehiculo", "repuesto", "estadisticas"],
                            "description": "Tipo de información a consultar: 'trabajo' para trabajos, 'cliente' para clientes, 'vehiculo' para vehículos, 'repuesto' para repuestos/inventario (devuelve SOLO el count total), 'estadisticas' para estadísticas generales"
                        },
                        "filtro": {
                            "type": "string",
                            "description": "Filtro de búsqueda opcional: ID, nombre, placa, RUT, etc. Dejar vacío para contar/listar todos. Para contar el total de registros, DEJAR VACÍO."
                        },
                        "detalle": {
                            "type": "boolean",
                            "description": "Si se requiere información detallada (default: false). Para contar registros, usar false o omitir."
                        }
                    },
                    "required": ["tipo"]
                }
            },
            {
                "type": "function",
                "name": "listado_trabajos",
                "description": "Lista todos los trabajos del taller mecánico con todos sus campos y detalles. Úsala cuando el usuario pida: 'muéstrame los trabajos', 'búscame trabajos', 'listado de trabajos', 'trabajos del taller', 'ver trabajos', o cualquier variación de estas frases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "estado": {
                            "type": "string",
                            "enum": ["todos", "activos", "completados", "entregados", "iniciado", "trabajando"],
                            "description": "Filtro por estado: 'todos' para todos los trabajos, 'activos' para iniciados y trabajando, o un estado específico"
                        },
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de trabajos a listar (default: 20, máximo recomendado: 50)"
                        }
                    },
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "listado_mecanicos",
                "description": "Lista todos los mecánicos del taller mecánico con todos sus campos y detalles. Úsala cuando el usuario pida: 'muéstrame los mecánicos', 'búscame mecánicos', 'listado de mecánicos', 'mecánicos del taller', 'ver mecánicos', o cualquier variación de estas frases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "activo": {
                            "type": "boolean",
                            "description": "Filtro por estado activo: true para solo activos, false para solo inactivos, null/omitir para todos"
                        },
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de mecánicos a listar (default: 50, máximo recomendado: 100)"
                        }
                    },
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "test_function_call",
                "description": "Función de test simple para diagnosticar problemas con function_calls. No requiere parámetros. Úsala cuando quieras probar si las function_calls funcionan correctamente.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "test2",
                "description": "Función de test para diagnosticar problemas de conexión a la base de datos. Se conecta a la tabla Mecanico y lista los nombres. Genera logs detallados. No requiere parámetros.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "netgogo",
                "description": "Activa el modo netgogo. Úsala cuando el usuario diga 'netgogo', 'ahora trabajaremos con netgogo', 'activa netgogo' o similar. Esta función confirma que se usarán las function_calls disponibles y lista todas las herramientas. Es importante activarla al inicio de una sesión de trabajo con herramientas.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "listado_clientes",
                "description": "Lista todos los clientes del taller mecánico con todos sus campos y detalles. Úsala cuando el usuario pida: 'muéstrame los clientes', 'búscame clientes', 'listado de clientes', 'clientes del taller', 'ver clientes', o cualquier variación de estas frases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "activo": {
                            "type": "boolean",
                            "description": "Filtro por estado activo: true para solo activos, false para solo inactivos, null/omitir para todos"
                        },
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de clientes a listar (default: 50, máximo recomendado: 100)"
                        },
                        "filtro": {
                            "type": "string",
                            "description": "Filtro de búsqueda opcional por RUT o nombre del cliente"
                        }
                    },
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "listado_vehiculos",
                "description": "Lista todos los vehículos del taller mecánico con todos sus campos y detalles. Úsala cuando el usuario pida: 'muéstrame los vehículos', 'búscame vehículos', 'listado de vehículos', 'vehículos del taller', 'ver vehículos', o cualquier variación de estas frases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de vehículos a listar (default: 50, máximo recomendado: 100)"
                        },
                        "filtro": {
                            "type": "string",
                            "description": "Filtro de búsqueda opcional por placa, marca, modelo o cliente"
                        }
                    },
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "listado_componentes",
                "description": "Lista todos los componentes del sistema con todos sus campos y detalles. Úsala cuando el usuario pida: 'muéstrame los componentes', 'búscame componentes', 'listado de componentes', 'componentes del sistema', 'ver componentes', o cualquier variación de estas frases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "activo": {
                            "type": "boolean",
                            "description": "Filtro por estado activo: true para solo activos, false para solo inactivos, null/omitir para todos"
                        },
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de componentes a listar (default: 100, máximo recomendado: 200)"
                        },
                        "filtro": {
                            "type": "string",
                            "description": "Filtro de búsqueda opcional por nombre o código del componente"
                        }
                    },
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "sugerir_componentes_por_descripcion",
                "description": "Sugiere componentes relevantes basados en la descripción del problema. Analiza la descripción para identificar acciones mencionadas (como 'cambio', 'reparación', 'falla', etc.) y busca componentes que tienen esas acciones asociadas con tarifas en el sistema. Úsala ESPECIALMENTE en la sección de componentes cuando el usuario haya descrito un problema. Esta función es más inteligente que listado_componentes porque busca basándose en acciones y componentes asociados.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "descripcion": {
                            "type": "string",
                            "description": "Descripción del problema o síntoma del vehículo. Ejemplos: 'falla de frenos', 'cambio de bujías', 'ruido en el motor', 'reparación de transmisión', etc."
                        },
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de componentes a sugerir (default: 20)"
                        }
                    },
                    "required": ["descripcion"]
                }
            },
            {
                "type": "function",
                "name": "listado_acciones",
                "description": "Lista todas las acciones disponibles en el sistema. Úsala cuando el usuario pida: 'muéstrame las acciones', 'búscame acciones', 'listado de acciones', 'acciones disponibles', 'ver acciones', o cualquier variación de estas frases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de acciones a listar (default: 100, máximo recomendado: 200)"
                        },
                        "filtro": {
                            "type": "string",
                            "description": "Filtro de búsqueda opcional por nombre de la acción"
                        }
                    },
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "listado_diagnosticos",
                "description": "Lista todos los diagnósticos del sistema con todos sus campos y detalles. Úsala cuando el usuario pida: 'muéstrame los diagnósticos', 'búscame diagnósticos', 'listado de diagnósticos', 'historial de diagnósticos', 'ver diagnósticos', o cualquier variación de estas frases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "estado": {
                            "type": "string",
                            "enum": ["pendiente", "aprobado", "rechazado"],
                            "description": "Filtro por estado: 'pendiente', 'aprobado', 'rechazado', o omitir para todos"
                        },
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de diagnósticos a listar (default: 50, máximo recomendado: 100)"
                        },
                        "filtro": {
                            "type": "string",
                            "description": "Filtro de búsqueda opcional por placa, marca o modelo del vehículo"
                        }
                    },
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "listado_compatibilidad",
                "description": "Lista información de compatibilidad entre repuestos y vehículos. Úsala cuando el usuario pida: 'compatibilidad de repuestos', 'repuestos compatibles', 'vehículos compatibles', 'ver compatibilidad', o cualquier variación de estas frases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repuesto_id": {
                            "type": "integer",
                            "description": "ID del repuesto para buscar vehículos compatibles (opcional)"
                        },
                        "vehiculo_id": {
                            "type": "integer",
                            "description": "ID del vehículo para buscar repuestos compatibles (opcional)"
                        },
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de resultados a listar (default: 50, máximo recomendado: 100)"
                        }
                    },
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "listado_compras",
                "description": "Lista todas las compras del sistema con todos sus campos y detalles. Úsala cuando el usuario pida: 'muéstrame las compras', 'búscame compras', 'listado de compras', 'compras del taller', 'ver compras', o cualquier variación de estas frases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "estado": {
                            "type": "string",
                            "enum": ["borrador", "confirmada", "recibida", "cancelada"],
                            "description": "Filtro por estado: 'borrador', 'confirmada', 'recibida', 'cancelada', o omitir para todos"
                        },
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de compras a listar (default: 50, máximo recomendado: 100)"
                        },
                        "filtro": {
                            "type": "string",
                            "description": "Filtro de búsqueda opcional por número de compra o proveedor"
                        }
                    },
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "listado_inventario",
                "description": "Lista el inventario de repuestos con información de stock. Busca en la tabla 'repuestos' y obtiene el stock de 'repuestos_en_stock'. Úsala cuando el usuario pida: 'muéstrame el inventario', 'búscame repuestos en stock', 'listado de inventario', 'inventario del taller', 'ver inventario', 'stock de repuestos', 'buscar repuesto', o cualquier variación de estas frases. Busca por nombre, SKU, código de barras, marca, referencia o descripción. IMPORTANTE: NO uses esta función para contar el total de registros de la tabla repuestos. Para contar registros, usa 'query_sistema' con tipo='repuesto'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limite": {
                            "type": "integer",
                            "description": "Número máximo de repuestos a listar (default: 200 para cubrir todos los registros, máximo recomendado: 500)"
                        },
                        "filtro": {
                            "type": "string",
                            "description": "Filtro de búsqueda opcional por nombre, SKU, código de barras, marca, referencia o descripción del repuesto. La búsqueda es case-insensitive y busca en todos estos campos."
                        },
                        "stock_minimo": {
                            "type": "integer",
                            "description": "Filtrar solo repuestos con stock menor o igual a este valor (opcional, útil para detectar stock bajo)"
                        }
                    },
                    "required": []
                }
            }
        ]
        
    def _validate_path(self, path):
        """Valida que la ruta esté dentro del proyecto"""
        base_path = Path(__file__).parent.parent.parent.absolute()
        resolved_path = (base_path / path).resolve()
        
        # Asegurar que está dentro del proyecto
        try:
            resolved_path.relative_to(base_path)
            return str(resolved_path)
        except ValueError:
            raise ValueError(f"Ruta fuera del proyecto: {path}")
    
    def list_files_in_dir(self, directory="."):
        """Lista los archivos que existen en un directorio dado"""
        try:
            validated_dir = self._validate_path(directory)
            files = os.listdir(validated_dir)
            return {"files": files}
        except Exception as e:
            return {"error": str(e)}
        
    def read_file(self, path):
        """Lee el contenido de un archivo en una ruta especificada"""
        try:
            validated_path = self._validate_path(path)
            with open(validated_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            err = f"Error al leer el archivo {path}: {str(e)}"
            return err
        
    def edit_file(self, path, prev_text, new_text):
        """Edita el contenido de un archivo reemplazando prev_text por new_text"""
        try:
            validated_path = self._validate_path(path)
            existed = os.path.exists(validated_path)
            
            if existed and prev_text:
                content = self.read_file(path)
                
                if isinstance(content, dict) and "error" in content:
                    return content["error"]
                
                if prev_text not in content:
                    return f"Texto '{prev_text[:50]}...' no encontrado en el archivo"
                
                content = content.replace(prev_text, new_text)
            else:
                # Crear o sobreescribir con el nuevo texto directamente
                dir_name = os.path.dirname(validated_path)
                if dir_name:
                    os.makedirs(dir_name, exist_ok=True)
                
                content = new_text
                
            with open(validated_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            action = "editado" if existed and prev_text else "creado"
            return f"Archivo {path} {action} exitosamente"
        except Exception as e:
            err = f"Error al crear o editar el archivo {path}: {str(e)}"
            return err
        
    def process_response(self, response_data):
        """
        Procesa la respuesta de la API de OpenAI
        Retorna: (called_tool: bool, tool_info: dict, final_message: str)
        """
        called_tool = False
        tool_info = None
        final_message = None
        
        # La respuesta puede tener diferentes estructuras dependiendo de la API
        # Asumimos que tiene un campo 'output' con una lista de outputs
        outputs = response_data.get('output', [])
        
        if not outputs:
            # Si no hay outputs, puede ser una respuesta directa
            if 'message' in response_data:
                final_message = response_data['message']
            return False, None, final_message
        
        for output in outputs:
            if isinstance(output, dict):
                output_type = output.get('type', '')
                
                if output_type == "function_call":
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
                    
                    # Ejecutar la herramienta
                    if fn_name == "list_files_in_dir":
                        result = self.list_files_in_dir(**args)
                    elif fn_name == "read_file":
                        result = self.read_file(**args)
                    elif fn_name == "edit_file":
                        result = self.edit_file(**args)
                    elif fn_name == "query_sistema":
                        # Esta función se ejecuta desde views_ia.py con acceso al request
                        # Aquí solo marcamos que se debe ejecutar
                        result = {"pending": True, "function": "query_sistema", "arguments": args}
                    else:
                        result = {"error": f"Herramienta desconocida: {fn_name}"}
                    
                    # Agregar resultado al historial
                    self.messages.append({
                        "type": "function_call_output",
                        "call_id": output.get('call_id', ''),
                        "output": json.dumps({
                            "result": result if isinstance(result, dict) else {"result": result}
                        })
                    })
                    
                    tool_info['result'] = result
                    return True, tool_info, None
                    
                elif output_type == "message":
                    # Extraer el mensaje
                    content = output.get('content', [])
                    if isinstance(content, list):
                        message_parts = []
                        for part in content:
                            if isinstance(part, dict):
                                if 'text' in part:
                                    message_parts.append(part['text'])
                                elif 'content' in part:
                                    message_parts.append(str(part['content']))
                            else:
                                message_parts.append(str(part))
                        final_message = "\n".join(message_parts)
                    elif isinstance(content, str):
                        final_message = content
                    else:
                        final_message = str(content)
        
        return called_tool, tool_info, final_message
    
    def activate_netgogo_mode(self):
        """Activa el modo netgogo y confirma que se usarán las function_calls"""
        # Listar herramientas disponibles
        herramientas = [
            "list_files_in_dir - Lista archivos en directorio",
            "read_file - Lee archivos del proyecto",
            "edit_file - Edita/crea archivos",
            "query_sistema - Consulta trabajos, clientes, vehículos, repuestos, estadísticas",
            "listado_trabajos - Lista trabajos del taller",
            "listado_mecanicos - Lista mecánicos del taller",
            "listado_clientes - Lista clientes del taller",
            "listado_vehiculos - Lista vehículos del taller",
            "listado_componentes - Lista componentes del sistema",
            "listado_acciones - Lista acciones disponibles",
            "listado_diagnosticos - Lista diagnósticos (historial)",
            "listado_compatibilidad - Consulta compatibilidad repuestos-vehículos",
            "listado_compras - Lista compras del taller",
            "listado_inventario - Lista inventario de repuestos con stock",
            "test_function_call - Prueba de function calls",
            "test2 - Prueba de conexión a BD"
        ]
        
        # Actualizar mensaje del sistema para priorizar herramientas
        modo_activo_msg = (
            "MODO NETGOGO ACTIVADO: Debes priorizar el uso de function_calls disponibles. "
            "Cuando el usuario solicite información del sistema, trabajos, mecánicos, clientes, "
            "vehículos o repuestos, DEBES usar las herramientas correspondientes (query_sistema, "
            "listado_trabajos, listado_mecanicos, etc.) en lugar de responder sin datos. "
            "Siempre usa las herramientas cuando sea apropiado."
        )
        
        # Actualizar el mensaje del sistema
        for i, msg in enumerate(self.messages):
            if msg.get('role') == 'system':
                self.messages[i]['content'] = modo_activo_msg
                break
        else:
            # Si no existe mensaje de sistema, agregarlo
            self.messages.insert(0, {"role": "system", "content": modo_activo_msg})
        
        return {
            "success": True,
            "message": "✅ MODO NETGOGO ACTIVADO",
            "confirmacion": "Estoy en modo netgogo y usaré las function_calls disponibles para todas tus consultas.",
            "herramientas_disponibles": herramientas,
            "instrucciones": "Ahora puedes preguntarme sobre trabajos, mecánicos, clientes, vehículos, repuestos o estadísticas, y usaré las herramientas correspondientes."
        }







