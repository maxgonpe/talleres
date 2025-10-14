#!/usr/bin/env python3
"""
Script simple para importar solo componentes desde el backup
"""

import os
import sys
import django
import re

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from car.models import Componente

def limpiar_texto(texto):
    """Limpia texto de PostgreSQL para SQLite"""
    if texto is None or texto == '\\N':
        return None
    texto = str(texto).replace('\\N', '')
    return texto.strip() if texto else None

def importar_componentes():
    """Importa componentes desde el backup"""
    print("🔄 Importando componentes...")
    
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
                # Verificar si ya existe
                if Componente.objects.filter(id=int(campos[0])).exists():
                    continue
                    
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
                # Verificar si ya existe
                if Componente.objects.filter(id=int(campos[0])).exists():
                    continue
                    
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

def main():
    """Función principal"""
    print("🚀 Importando componentes de SolutionCar...")
    print("=" * 50)
    
    try:
        importar_componentes()
        print()
        
        print("=" * 50)
        print("✅ Importación completada!")
        print()
        print("📊 Resumen:")
        print(f"   • Componentes: {Componente.objects.count()}")
        print()
        print("🎯 Ahora puedes probar el algoritmo de relación inteligente!")
        
    except Exception as e:
        print(f"❌ Error durante la importación: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
