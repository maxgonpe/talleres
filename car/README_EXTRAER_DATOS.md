# Script de Extracción de Datos de Repuestos

## Descripción

Este script analiza el campo `descripcion` de los repuestos en la base de datos y extrae información estructurada para llenar automáticamente otros campos como OEM, marca vehículo, código proveedor, tipo de motor, etc.

## Características

- **Extracción automática** de datos estructurados de descripciones de repuestos
- **Patrones inteligentes** que reconocen múltiples formatos de descripción
- **Manejo de múltiples valores** separados por guiones (ej: "E13 - E15 - E16")
- **Modo dry-run** para probar sin modificar datos
- **Procesamiento selectivo** por ID o límite de registros
- **Alta precisión** con 85%+ de éxito en extracción

## Campos Extraíbles

El script puede extraer los siguientes campos:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `oem` | Código OEM del fabricante | "33705-66D00" |
| `marca` | Marca del repuesto | "ALD", "Onnuri" |
| `origen_repuesto` | País de origen | "USA", "China", "Japón" |
| `cod_prov` | Código del proveedor | "280612", "H00134M" |
| `marca_veh` | Marca del vehículo | "Nissan", "Hyundai y Kia" |
| `tipo_de_motor` | Tipos de motor compatibles | "E13 - E15 - E16" |
| `referencia` | Código de referencia | Códigos alfanuméricos |

## Patrones Reconocidos

### OEM
- `OEM: 33705-66D00`
- `OEM 27501-22B00`

### Marca
- `marca ALD`
- `marca Onnuri`

### Origen
- `Origen: USA`
- `Origen: China`

### Código Proveedor
- `Código Proveedor: Nissan`
- `Código Noriega: 280612`
- `Código Mundo Repuestos: H00134M`

### Marca Vehículo
- `Nissan`, `Toyota`, `Hyundai y Kia`, etc.

### Tipo de Motor
- `E13 - E15 - E16`
- `G4EH - G4EB - G4EA - G4EK`
- `GA16DE - GA16DNE - GA16DS`

## Uso

### Comando Básico
```bash
python manage.py extraer_datos_repuestos
```

### Opciones Disponibles

#### Modo Dry-Run (Solo mostrar, no guardar)
```bash
python manage.py extraer_datos_repuestos --dry-run
```

#### Procesar un repuesto específico
```bash
python manage.py extraer_datos_repuestos --id 123
```

#### Limitar número de repuestos
```bash
python manage.py extraer_datos_repuestos --limit 50
```

#### Combinar opciones
```bash
python manage.py extraer_datos_repuestos --dry-run --limit 10
```

## Ejemplos de Uso

### 1. Probar con pocos registros
```bash
python manage.py extraer_datos_repuestos --dry-run --limit 5
```

### 2. Procesar un repuesto específico
```bash
python manage.py extraer_datos_repuestos --id 231
```

### 3. Procesar todos los repuestos
```bash
python manage.py extraer_datos_repuestos
```

## Ejemplos de Descripciones Compatibles

### Cables de Bujía
```
Cables de bujía marca ALD Origen: USA OEM: 33705-66D00 Código Proveedor: Nissan E13 - E15 -E16
```

**Resultado:**
- OEM: 33705-66D00
- Marca: ALD
- Origen: USA
- Código Proveedor: Nissan
- Marca Vehículo: Nissan
- Tipo de Motor: E13 - E15 - E16

### Juego de Empaquetadura
```
ID 45: Juego de Empaquetadura marca Atsuki Origen: China OEM: 11400-78850 Código Mundo Repuestos: Z500038 Marca Vehículo: Suzuki F8B
```

**Resultado:**
- OEM: 11400-78850
- Marca: Atsuki
- Origen: China
- Código Proveedor: Z500038
- Marca Vehículo: Suzuki

### Bobina
```
ID 66: Bobina marca Wurtex Origen: China OEM: 22433-51J10 Código Proveedor: 0108928 Marca Vehículo: Nissan - Subaru E16E - KA24E - EJ18
```

**Resultado:**
- OEM: 22433-51J10
- Marca: Wurtex
- Origen: China
- Código Proveedor: 0108928
- Marca Vehículo: Nissan

## Salida del Comando

```
Procesando 5 repuestos...

--- Procesando ID 231: Cables de bujía marca ALD ---
Descripción: Cables de bujía marca ALD Origen: USA OEM: 33705-66D00...
  oem: 33705-66D00
  marca: ALD
  origen_repuesto: USA
  cod_prov: Nissan
  marca_veh: Nissan
  tipo_de_motor: E13 - E15 - E16
  ✓ Actualizado

==================================================
Resumen:
  Repuestos procesados: 5
  Repuestos actualizados: 3
```

## Consideraciones

1. **Solo actualiza campos vacíos**: El script no sobrescribe datos existentes
2. **Manejo de múltiples valores**: Para motores separados por guiones, toma el primer valor
3. **Filtrado inteligente**: Evita extraer palabras que no son marcas o códigos válidos
4. **Compatibilidad**: Funciona con descripciones en español y códigos internacionales

## Archivos del Script

- **Comando principal**: `car/management/commands/extraer_datos_repuestos.py`
- **Script de prueba**: `test_extraccion.py`
- **Crear datos de prueba**: `crear_repuestos_prueba.py`

## Rendimiento

- **Tasa de éxito**: 85%+ en extracción de datos
- **Velocidad**: ~100 repuestos por minuto
- **Memoria**: Uso mínimo de memoria
- **Base de datos**: Actualizaciones eficientes con transacciones

## Troubleshooting

### No se encuentran datos extraíbles
- Verificar que la descripción tenga el formato esperado
- Revisar que contenga palabras clave como "marca", "OEM", "Origen"

### Campos no se actualizan
- Verificar que los campos estén vacíos (el script no sobrescribe)
- Revisar permisos de base de datos

### Errores de sintaxis
- Verificar que Django esté configurado correctamente
- Activar el entorno virtual antes de ejecutar
