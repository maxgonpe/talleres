#!/usr/bin/env python3
"""
Script para inyectar 200 registros de repuestos ficticios en la base de datos local.
Esto nos ayudará a probar el rendimiento de la búsqueda con muchos registros.
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from car.models import Repuesto

def generar_repuestos_ficticios(cantidad=200):
    """Genera repuestos ficticios con datos realistas"""
    
    # Datos de ejemplo
    marcas = ['TOYOTA', 'HONDA', 'NISSAN', 'FORD', 'CHEVROLET', 'VOLKSWAGEN', 'BMW', 'MERCEDES', 'AUDI', 'HYUNDAI']
    origenes = ['ORIGINAL', 'COMPATIBLE', 'GENÉRICO', 'REMANUFACTURADO', 'USADO']
    posiciones = ['DELANTERA', 'TRASERA', 'IZQUIERDA', 'DERECHA', 'CENTRAL', 'SUPERIOR', 'INFERIOR']
    unidades = ['PZA', 'SET', 'KIT', 'PAR', 'LITRO', 'KG', 'MTS']
    tipos_motor = ['1.6', '1.8', '2.0', '2.4', '3.0', 'DIESEL', 'HÍBRIDO', 'ELÉCTRICO']
    
    # Componentes comunes
    componentes = [
        'FILTRO DE AIRE', 'FILTRO DE ACEITE', 'FILTRO DE COMBUSTIBLE', 'FILTRO DE HABITÁCULO',
        'PASTILLAS DE FRENO', 'DISCOS DE FRENO', 'BOMBA DE AGUA', 'TERMOSTATO',
        'BOMBA DE COMBUSTIBLE', 'INYECTORES', 'BUJÍAS', 'CABLES DE BUJÍAS',
        'AMORTIGUADORES', 'BALLESTAS', 'ROTULAS', 'TERMINALES',
        'BOMBA DE DIRECCIÓN', 'CRESTA DE DIRECCIÓN', 'BOMBA DE FRENO', 'CILINDRO MAESTRO',
        'ALTERNADOR', 'MOTOR DE ARRANQUE', 'BATERÍA', 'FUSIBLES',
        'LÁMPARAS', 'BOMBILLAS', 'INTERRUPTORES', 'RELAYS',
        'SENSORES', 'ACTUADORES', 'VÁLVULAS', 'MANGUERAS',
        'CORREAS', 'POLEAS', 'RODAMIENTOS', 'RETENES',
        'JUNTAS', 'SELLOS', 'TAPONES', 'TUBOS'
    ]
    
    repuestos_creados = []
    
    print(f"🚀 Generando {cantidad} repuestos ficticios...")
    
    for i in range(cantidad):
        try:
            # Generar datos aleatorios
            componente = random.choice(componentes)
            marca = random.choice(marcas)
            origen = random.choice(origenes)
            posicion = random.choice(posiciones)
            unidad = random.choice(unidades)
            tipo_motor = random.choice(tipos_motor)
            
            # Generar SKU único
            sku = f"SKU{str(i+1).zfill(6)}"
            
            # Generar OEM
            oem = f"OEM{random.randint(100000, 999999)}"
            
            # Generar código de barras
            codigo_barra = f"{random.randint(1000000000000, 9999999999999)}"
            
            # Generar nombre
            nombre = f"{componente} {marca} {tipo_motor}"
            
            # Generar descripción
            descripcion = f"Repuesto {componente.lower()} para vehículos {marca} con motor {tipo_motor}"
            
            # Generar precios
            precio_costo = round(random.uniform(5000, 150000), 0)
            precio_venta = round(precio_costo * random.uniform(1.3, 2.5), 0)
            
            # Generar stock
            stock = random.randint(0, 50)
            
            # Crear repuesto
            repuesto = Repuesto.objects.create(
                sku=sku,
                oem=oem,
                referencia=f"REF{random.randint(1000, 9999)}",
                nombre=nombre,
                marca=marca,
                descripcion=descripcion,
                medida=f"{random.randint(10, 200)}x{random.randint(10, 200)}x{random.randint(5, 50)}",
                posicion=posicion,
                unidad=unidad,
                precio_costo=precio_costo,
                precio_venta=precio_venta,
                codigo_barra=codigo_barra,
                stock=stock,
                origen_repuesto=origen,
                cod_prov=f"PROV{random.randint(100, 999)}",
                marca_veh=marca,
                tipo_de_motor=tipo_motor
            )
            
            repuestos_creados.append(repuesto)
            
            if (i + 1) % 50 == 0:
                print(f"✅ Creados {i + 1} repuestos...")
                
        except Exception as e:
            print(f"❌ Error creando repuesto {i+1}: {e}")
            continue
    
    print(f"🎉 ¡Completado! Se crearon {len(repuestos_creados)} repuestos ficticios.")
    print(f"📊 Total de repuestos en la base de datos: {Repuesto.objects.count()}")
    
    return repuestos_creados

def limpiar_repuestos_ficticios():
    """Limpia los repuestos ficticios creados por este script"""
    print("🧹 Limpiando repuestos ficticios...")
    
    # Eliminar repuestos que empiecen con SKU
    repuestos_ficticios = Repuesto.objects.filter(sku__startswith='SKU')
    cantidad = repuestos_ficticios.count()
    repuestos_ficticios.delete()
    
    print(f"🗑️ Se eliminaron {cantidad} repuestos ficticios.")
    print(f"📊 Total de repuestos restantes: {Repuesto.objects.count()}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "limpiar":
        limpiar_repuestos_ficticios()
    else:
        generar_repuestos_ficticios(200)

