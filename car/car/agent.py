import os
import json
from pathlib import Path

class Agent:
    def __init__(self):
        self.setup_tools()
        self.messages = [
            {"role": "system", "content": "Eres un asistente útil que habla español y eres muy conciso con tus respuestas"}
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
                "description": "Consulta información del sistema del taller mecánico: trabajos, clientes, vehículos, repuestos y estadísticas. Úsala cuando el usuario pregunte sobre el estado del taller, trabajos activos, clientes, vehículos o inventario.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tipo": {
                            "type": "string",
                            "enum": ["trabajo", "cliente", "vehiculo", "repuesto", "estadisticas"],
                            "description": "Tipo de información a consultar: 'trabajo' para trabajos, 'cliente' para clientes, 'vehiculo' para vehículos, 'repuesto' para repuestos/inventario, 'estadisticas' para estadísticas generales"
                        },
                        "filtro": {
                            "type": "string",
                            "description": "Filtro de búsqueda opcional: ID, nombre, placa, RUT, etc. Dejar vacío para listar todos"
                        },
                        "detalle": {
                            "type": "boolean",
                            "description": "Si se requiere información detallada (default: false)"
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





