#!/usr/bin/env python
"""
Script de verificación para diagnosticar problemas con RUTs y vehículos.
Ejecutar desde el directorio del proyecto Django: python manage.py shell < verificar_rut_vehiculos.py
O ejecutar directamente: python verificar_rut_vehiculos.py (si está configurado el entorno Django)
"""

import os
import sys
import django

# Configurar Django
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    django.setup()

from car.models import Cliente_Taller, Vehiculo
from django.db.models import Q

def verificar_rut(rut):
    """Verifica un RUT específico y muestra información detallada"""
    print(f"\n{'='*60}")
    print(f"🔍 VERIFICANDO RUT: {rut}")
    print(f"{'='*60}")
    
    # Buscar cliente con ambas variantes
    rut_minuscula = rut[:-1] + 'k' if rut and rut[-1].lower() == 'k' else rut
    rut_mayuscula = rut[:-1] + 'K' if rut and rut[-1].lower() == 'k' else rut
    
    print(f"\n📋 Variantes a buscar:")
    print(f"   - Minúscula: '{rut_minuscula}'")
    print(f"   - Mayúscula: '{rut_mayuscula}'")
    
    # Buscar cliente
    cliente_min = Cliente_Taller.objects.filter(rut=rut_minuscula).first()
    cliente_may = Cliente_Taller.objects.filter(rut=rut_mayuscula).first()
    
    print(f"\n👤 Cliente encontrado:")
    if cliente_min:
        print(f"   ✅ Con minúscula '{rut_minuscula}': {cliente_min.nombre} (RUT en BD: '{cliente_min.rut}')")
    else:
        print(f"   ❌ Con minúscula '{rut_minuscula}': NO ENCONTRADO")
    
    if cliente_may:
        print(f"   ✅ Con mayúscula '{rut_mayuscula}': {cliente_may.nombre} (RUT en BD: '{cliente_may.rut}')")
    else:
        print(f"   ❌ Con mayúscula '{rut_mayuscula}': NO ENCONTRADO")
    
    # Buscar vehículos
    cliente = cliente_min or cliente_may
    if cliente:
        vehiculos = Vehiculo.objects.filter(cliente=cliente).order_by('placa')
        print(f"\n🚗 Vehículos asociados ({vehiculos.count()}):")
        if vehiculos.exists():
            for v in vehiculos:
                print(f"   - {v.placa} | {v.marca} {v.modelo} ({v.anio})")
        else:
            print(f"   ⚠️  El cliente no tiene vehículos asociados")
    else:
        print(f"\n❌ No se encontró el cliente, no se pueden buscar vehículos")
    
    # Buscar con Q object (como lo hace el código)
    print(f"\n🔍 Búsqueda con Q object (como en views.py):")
    vehiculos_q = Vehiculo.objects.filter(
        Q(cliente__rut=rut_minuscula) | Q(cliente__rut=rut_mayuscula)
    ).order_by('placa')
    print(f"   Vehículos encontrados: {vehiculos_q.count()}")
    for v in vehiculos_q:
        print(f"   - {v.placa} | Cliente RUT: '{v.cliente.rut}'")

def listar_ruts_con_k():
    """Lista todos los RUTs que terminan en 'k' o 'K'"""
    print(f"\n{'='*60}")
    print(f"📋 TODOS LOS RUTs QUE TERMINAN EN 'k' O 'K'")
    print(f"{'='*60}")
    
    clientes_k = Cliente_Taller.objects.filter(
        Q(rut__endswith='k') | Q(rut__endswith='K')
    ).order_by('rut')
    
    print(f"\nTotal encontrados: {clientes_k.count()}")
    print(f"\nDetalle:")
    for cliente in clientes_k:
        vehiculos_count = Vehiculo.objects.filter(cliente=cliente).count()
        print(f"  - RUT: '{cliente.rut}' | Nombre: {cliente.nombre} | Vehículos: {vehiculos_count}")

def verificar_formato_ruts():
    """Verifica el formato de los RUTs en la BD"""
    print(f"\n{'='*60}")
    print(f"📋 VERIFICACIÓN DE FORMATO DE RUTs")
    print(f"{'='*60}")
    
    total = Cliente_Taller.objects.count()
    con_k_minuscula = Cliente_Taller.objects.filter(rut__endswith='k').exclude(rut__endswith='K').count()
    con_k_mayuscula = Cliente_Taller.objects.filter(rut__endswith='K').count()
    con_guion = Cliente_Taller.objects.filter(rut__contains='-').count()
    sin_guion = total - con_guion
    
    print(f"\nTotal de clientes: {total}")
    print(f"  - Con 'k' minúscula: {con_k_minuscula}")
    print(f"  - Con 'K' mayúscula: {con_k_mayuscula}")
    print(f"  - Con guión: {con_guion}")
    print(f"  - Sin guión: {sin_guion}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔧 SCRIPT DE VERIFICACIÓN DE RUTs Y VEHÍCULOS")
    print("="*60)
    
    # Verificar formato general
    verificar_formato_ruts()
    
    # Listar RUTs con k/K
    listar_ruts_con_k()
    
    # Verificar RUTs específicos mencionados por el usuario
    print(f"\n{'='*60}")
    print(f"🔍 VERIFICANDO RUTs ESPECÍFICOS DEL PROBLEMA")
    print(f"{'='*60}")
    
    ruts_problema = ['15056879k', '15056879K', '24518798k', '24518798K']
    for rut in ruts_problema:
        verificar_rut(rut)
    
    print(f"\n{'='*60}")
    print(f"✅ VERIFICACIÓN COMPLETA")
    print(f"{'='*60}\n")
