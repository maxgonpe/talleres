#!/usr/bin/env python3
"""
Script para importar datos de SolutionCar desde el backup PostgreSQL a SQLite local
"""

import os
import sys
import django
import re
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from car.models import Repuesto, Componente, ComponenteAccion, Accion, ComponenteRepuesto, RepuestoEnStock

def limpiar_texto(texto):
    """Limpia texto de PostgreSQL para SQLite"""
    if texto is None or texto == '\\N':
        return None
    # Remover caracteres de escape de PostgreSQL
    texto = str(texto).replace('\\N', '')
    return texto.strip() if texto else None

def parsear_fecha(fecha_str):
    """Convierte fecha de PostgreSQL a formato Python"""
    if not fecha_str or fecha_str == '\\N':
        return None
    try:
        # Formato: 2025-10-07 13:34:02.494534+00
        fecha_str = fecha_str.split('+')[0]  # Remover timezone
        return datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S.%f')
    except:
        try:
            return datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
        except:
            return None

def importar_repuestos():
    """Importa repuestos desde el backup"""
    print("🔄 Importando repuestos...")
    
    # Limpiar relaciones existentes primero
    from car.models import ComponenteRepuesto, DiagnosticoRepuesto, TrabajoRepuesto, CompraItem, VentaItem
    ComponenteRepuesto.objects.all().delete()
    DiagnosticoRepuesto.objects.all().delete()
    TrabajoRepuesto.objects.all().delete()
    CompraItem.objects.all().delete()
    VentaItem.objects.all().delete()
    print("   ✅ Relaciones existentes eliminadas")
    
    # Limpiar repuestos existentes
    Repuesto.objects.all().delete()
    print("   ✅ Repuestos existentes eliminados")
    
    with open('cliente_solutioncar_db.sql', 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Buscar la sección de repuestos
    patron = r'COPY public\.car_repuesto.*?FROM stdin;\n(.*?)\n\\\.'
    match = re.search(patron, contenido, re.DOTALL)
    
    if not match:
        print("   ❌ No se encontraron datos de repuestos")
        return
    
    lineas = match.group(1).strip().split('\n')
    repuestos_importados = 0
    
    for linea in lineas:
        if not linea.strip() or linea.startswith('\\'):
            continue
            
        # Parsear línea (formato tab-separated)
        campos = linea.split('\t')
        
        if len(campos) < 19:
            continue
            
        try:
            repuesto = Repuesto(
                id=int(campos[0]),
                sku=limpiar_texto(campos[1]),
                oem=limpiar_texto(campos[2]),
                referencia=limpiar_texto(campos[3]),
                nombre=limpiar_texto(campos[4]) or 'Sin nombre',
                marca=limpiar_texto(campos[5]) or 'general',
                descripcion=limpiar_texto(campos[6]) or 'Sin descripción',
                medida=limpiar_texto(campos[7]) or 'Sin medida',
                posicion=limpiar_texto(campos[8]) or 'Sin posición',
                unidad=limpiar_texto(campos[9]) or 'pieza',
                precio_costo=float(campos[10]) if campos[10] and campos[10] != '\\N' else None,
                precio_venta=float(campos[11]) if campos[11] and campos[11] != '\\N' else None,
                created=parsear_fecha(campos[12]),
                codigo_barra=limpiar_texto(campos[13]),
                stock=int(campos[14]) if campos[14] and campos[14] != '\\N' else 0,
                cod_prov=limpiar_texto(campos[15]),
                marca_veh=limpiar_texto(campos[16]) or 'xxx',
                origen_repuesto=limpiar_texto(campos[17]) or 'sin-origen',
                tipo_de_motor=limpiar_texto(campos[18]) or 'zzzzzz'
            )
            repuesto.save()
            repuestos_importados += 1
            
        except Exception as e:
            print(f"   ⚠️  Error importando repuesto: {e}")
            continue
    
    print(f"   ✅ {repuestos_importados} repuestos importados")

def importar_componentes():
    """Importa componentes desde el backup"""
    print("🔄 Importando componentes...")
    
    # Limpiar relaciones de componentes primero
    from car.models import ComponenteAccion, DiagnosticoComponenteAccion, TrabajoAccion
    ComponenteAccion.objects.all().delete()
    DiagnosticoComponenteAccion.objects.all().delete()
    TrabajoAccion.objects.all().delete()
    print("   ✅ Relaciones de componentes eliminadas")
    
    # Limpiar componentes existentes (primero hijos, luego padres)
    Componente.objects.filter(padre__isnull=False).delete()
    Componente.objects.filter(padre__isnull=True).delete()
    print("   ✅ Componentes existentes eliminados")
    
    with open('cliente_solutioncar_db.sql', 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Buscar la sección de componentes
    patron = r'COPY public\.car_componente.*?FROM stdin;\n(.*?)\n\\\.'
    match = re.search(patron, contenido, re.DOTALL)
    
    if not match:
        print("   ❌ No se encontraron datos de componentes")
        return
    
    lineas = match.group(1).strip().split('\n')
    componentes_importados = 0
    componentes_por_id = {}
    
    # Primera pasada: crear componentes sin padre
    for linea in lineas:
        if not linea.strip() or linea.startswith('\\'):
            continue
            
        campos = linea.split('\t')
        if len(campos) < 5:
            continue
            
        try:
            padre_id = int(campos[4]) if campos[4] and campos[4] != '\\N' else None
            
            if padre_id is None:  # Solo componentes padre
                componente = Componente(
                    id=int(campos[0]),
                    nombre=limpiar_texto(campos[1]) or 'Sin nombre',
                    codigo=limpiar_texto(campos[2]) or '',
                    activo=campos[3] == 't',
                    padre=None
                )
                componente.save()
                componentes_por_id[componente.id] = componente
                componentes_importados += 1
                
        except Exception as e:
            print(f"   ⚠️  Error importando componente padre: {e}")
            continue
    
    # Segunda pasada: crear componentes con padre
    for linea in lineas:
        if not linea.strip() or linea.startswith('\\'):
            continue
            
        campos = linea.split('\t')
        if len(campos) < 5:
            continue
            
        try:
            padre_id = int(campos[4]) if campos[4] and campos[4] != '\\N' else None
            
            if padre_id is not None:  # Componentes hijo
                padre = componentes_por_id.get(padre_id)
                if padre:
                    componente = Componente(
                        id=int(campos[0]),
                        nombre=limpiar_texto(campos[1]) or 'Sin nombre',
                        codigo=limpiar_texto(campos[2]) or '',
                        activo=campos[3] == 't',
                        padre=padre
                    )
                    componente.save()
                    componentes_por_id[componente.id] = componente
                    componentes_importados += 1
                
        except Exception as e:
            print(f"   ⚠️  Error importando componente hijo: {e}")
            continue
    
    print(f"   ✅ {componentes_importados} componentes importados")

def importar_stock():
    """Importa stock de repuestos"""
    print("🔄 Importando stock de repuestos...")
    
    # Limpiar stock existente
    RepuestoEnStock.objects.all().delete()
    print("   ✅ Stock existente eliminado")
    
    with open('cliente_solutioncar_db.sql', 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Buscar la sección de stock
    patron = r'COPY public\.car_repuestoenstock.*?FROM stdin;\n(.*?)\n\\\.'
    match = re.search(patron, contenido, re.DOTALL)
    
    if not match:
        print("   ❌ No se encontraron datos de stock")
        return
    
    lineas = match.group(1).strip().split('\n')
    stock_importado = 0
    
    for linea in lineas:
        if not linea.strip() or linea.startswith('\\'):
            continue
            
        campos = linea.split('\t')
        if len(campos) < 9:
            continue
            
        try:
            repuesto_id = int(campos[8])
            repuesto = Repuesto.objects.filter(id=repuesto_id).first()
            
            if repuesto:
                stock = RepuestoEnStock(
                    repuesto=repuesto,
                    deposito=limpiar_texto(campos[1]) or 'bodega-principal',
                    proveedor=limpiar_texto(campos[2]) or '',
                    stock=int(campos[3]) if campos[3] and campos[3] != '\\N' else 0,
                    reservado=int(campos[4]) if campos[4] and campos[4] != '\\N' else 0,
                    precio_compra=float(campos[5]) if campos[5] and campos[5] != '\\N' else None,
                    precio_venta=float(campos[6]) if campos[6] and campos[6] != '\\N' else None,
                    ultima_actualizacion=parsear_fecha(campos[7])
                )
                stock.save()
                stock_importado += 1
                
        except Exception as e:
            print(f"   ⚠️  Error importando stock: {e}")
            continue
    
    print(f"   ✅ {stock_importado} registros de stock importados")

def main():
    """Función principal"""
    print("🚀 Iniciando importación de datos de SolutionCar...")
    print("=" * 50)
    
    try:
        importar_repuestos()
        print()
        importar_componentes()
        print()
        importar_stock()
        print()
        
        print("=" * 50)
        print("✅ Importación completada exitosamente!")
        print()
        print("📊 Resumen:")
        print(f"   • Repuestos: {Repuesto.objects.count()}")
        print(f"   • Componentes: {Componente.objects.count()}")
        print(f"   • Stock: {RepuestoEnStock.objects.count()}")
        print()
        print("🎯 Ahora puedes probar el algoritmo de relación inteligente!")
        
    except Exception as e:
        print(f"❌ Error durante la importación: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
