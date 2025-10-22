#!/usr/bin/env python3
"""
Script para probar la vista de compra 13
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from car.models import Compra, CompraItem

def probar_vista_compra_13():
    print("🔍 PROBANDO VISTA DE COMPRA 13")
    print("=" * 60)
    
    try:
        # 1. OBTENER COMPRA 13
        print("📊 OBTENIENDO COMPRA 13...")
        
        compra = Compra.objects.get(pk=13)
        print(f"  Compra: {compra.numero_compra} (ID: {compra.id})")
        print(f"  Proveedor: {compra.proveedor}")
        print(f"  Estado: {compra.estado}")
        print(f"  Total: ${compra.total}")
        
        # 2. OBTENER ITEMS DE LA COMPRA
        print(f"\n📦 OBTENIENDO ITEMS DE LA COMPRA...")
        
        items = compra.items.all().order_by('repuesto__nombre')
        print(f"  Items encontrados: {items.count()}")
        
        if items.exists():
            for item in items:
                print(f"    Item ID: {item.id}")
                print(f"      Repuesto: {item.repuesto.nombre}")
                print(f"      SKU: {item.repuesto.sku}")
                print(f"      Cantidad: {item.cantidad}")
                print(f"      Precio unitario: ${item.precio_unitario}")
                print(f"      Subtotal: ${item.subtotal}")
                print(f"      Recibido: {item.recibido}")
                print(f"      ---")
        else:
            print(f"  ❌ No hay items en la compra")
            
            # Verificar si hay items en la base de datos directamente
            print(f"\n🔍 VERIFICANDO BASE DE DATOS DIRECTAMENTE...")
            
            items_db = CompraItem.objects.filter(compra_id=13)
            print(f"  Items en BD: {items_db.count()}")
            
            for item in items_db:
                print(f"    Item ID: {item.id}")
                print(f"      Compra ID: {item.compra_id}")
                print(f"      Repuesto ID: {item.repuesto_id}")
                print(f"      Cantidad: {item.cantidad}")
                print(f"      Precio unitario: ${item.precio_unitario}")
                print(f"      Subtotal: ${item.subtotal}")
                print(f"      Recibido: {item.recibido}")
                print(f"      ---")
        
        # 3. VERIFICAR RELACIÓN
        print(f"\n🔗 VERIFICANDO RELACIÓN...")
        
        print(f"  compra.items.all(): {compra.items.all().count()}")
        print(f"  CompraItem.objects.filter(compra=compra): {CompraItem.objects.filter(compra=compra).count()}")
        print(f"  CompraItem.objects.filter(compra_id=compra.id): {CompraItem.objects.filter(compra_id=compra.id).count()}")
        
        # 4. PROBAR DIFERENTES CONSULTAS
        print(f"\n🧪 PROBANDO DIFERENTES CONSULTAS...")
        
        # Consulta 1: items del compra
        items1 = compra.items.all()
        print(f"  compra.items.all(): {items1.count()}")
        
        # Consulta 2: items por compra_id
        items2 = CompraItem.objects.filter(compra_id=compra.id)
        print(f"  CompraItem.objects.filter(compra_id=compra.id): {items2.count()}")
        
        # Consulta 3: items por compra
        items3 = CompraItem.objects.filter(compra=compra)
        print(f"  CompraItem.objects.filter(compra=compra): {items3.count()}")
        
        # 5. VERIFICAR SI HAY PROBLEMA CON EL MODELO
        print(f"\n🔍 VERIFICANDO MODELO...")
        
        print(f"  Compra model: {Compra.__name__}")
        print(f"  CompraItem model: {CompraItem.__name__}")
        print(f"  Compra.related_name: {Compra._meta.get_field('items').related_name}")
        
        # 6. CREAR ITEM DE PRUEBA SI NO EXISTE
        if items.count() == 0:
            print(f"\n📦 CREANDO ITEM DE PRUEBA...")
            
            from car.models import Repuesto
            
            # Buscar repuesto Aceite 10w-40
            repuesto = Repuesto.objects.filter(nombre__icontains='Aceite 10w-40').first()
            
            if repuesto:
                print(f"  Repuesto encontrado: {repuesto.nombre}")
                
                # Crear item
                item = CompraItem.objects.create(
                    compra=compra,
                    repuesto=repuesto,
                    cantidad=2,
                    precio_unitario=21800,
                    subtotal=43600,
                    recibido=False
                )
                
                print(f"  ✅ Item creado: ID {item.id}")
                print(f"    Cantidad: {item.cantidad}")
                print(f"    Precio unitario: ${item.precio_unitario}")
                print(f"    Subtotal: ${item.subtotal}")
                
                # Verificar que se creó correctamente
                items_nuevos = compra.items.all()
                print(f"  Items después de crear: {items_nuevos.count()}")
            else:
                print(f"  ❌ No se encontró el repuesto Aceite 10w-40")
        
        # 7. VERIFICAR RESULTADO FINAL
        print(f"\n🔍 VERIFICANDO RESULTADO FINAL...")
        
        items_final = compra.items.all().order_by('repuesto__nombre')
        print(f"  Items finales: {items_final.count()}")
        
        for item in items_final:
            print(f"    Item ID: {item.id}")
            print(f"      Repuesto: {item.repuesto.nombre}")
            print(f"      SKU: {item.repuesto.sku}")
            print(f"      Cantidad: {item.cantidad}")
            print(f"      Precio unitario: ${item.precio_unitario}")
            print(f"      Subtotal: ${item.subtotal}")
            print(f"      Recibido: {item.recibido}")
            print(f"      ---")
        
        print(f"\n🎉 ¡PRUEBA COMPLETADA!")
        print("Si los items aparecen aquí pero no en el template, el problema está en el template o en el JavaScript")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    probar_vista_compra_13()



