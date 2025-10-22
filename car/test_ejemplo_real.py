#!/usr/bin/env python3
"""
Script para probar el ejemplo real del usuario
Stock: 3 unidades, Precio costo: $19,278, Precio venta: $30,000
Compra: 4 unidades a $20,000 c/u
"""

from decimal import Decimal

def calcular_ejemplo_real():
    print("🧪 PRUEBA CON EJEMPLO REAL DEL USUARIO")
    print("=" * 60)
    
    # Estado inicial
    stock_anterior = 3
    precio_costo_anterior = Decimal('19278')
    precio_venta_anterior = Decimal('30000')
    
    print("📊 ESTADO INICIAL:")
    print(f"  Stock: {stock_anterior} unidades")
    print(f"  Precio costo: ${precio_costo_anterior}")
    print(f"  Precio venta: ${precio_venta_anterior}")
    
    # Calcular factor de margen
    factor_margen = precio_venta_anterior / precio_costo_anterior
    margen_porcentaje = (factor_margen - 1) * 100
    print(f"  Factor de margen: {factor_margen:.3f}")
    print(f"  Margen porcentual: {margen_porcentaje:.1f}%")
    
    print("")
    
    # Compra nueva
    cantidad_entrada = 4
    precio_compra_nuevo = Decimal('20000')
    
    print("🛒 COMPRA NUEVA:")
    print(f"  Cantidad: {cantidad_entrada} unidades")
    print(f"  Precio por unidad: ${precio_compra_nuevo}")
    
    print("")
    
    # Cálculo del nuevo precio costo (promedio ponderado)
    valor_anterior = stock_anterior * precio_costo_anterior
    valor_nuevo = cantidad_entrada * precio_compra_nuevo
    nuevo_stock = stock_anterior + cantidad_entrada
    nuevo_precio_costo = (valor_anterior + valor_nuevo) / nuevo_stock
    
    print("📈 CÁLCULO DEL NUEVO PRECIO COSTO:")
    print(f"  Valor anterior: {stock_anterior} × ${precio_costo_anterior} = ${valor_anterior}")
    print(f"  Valor nuevo: {cantidad_entrada} × ${precio_compra_nuevo} = ${valor_nuevo}")
    print(f"  Total valor: ${valor_anterior} + ${valor_nuevo} = ${valor_anterior + valor_nuevo}")
    print(f"  Nuevo stock: {stock_anterior} + {cantidad_entrada} = {nuevo_stock}")
    print(f"  Nuevo precio costo: ${valor_anterior + valor_nuevo} ÷ {nuevo_stock} = ${nuevo_precio_costo:.2f}")
    
    print("")
    
    # Cálculo del nuevo precio venta (aplicando factor de margen)
    nuevo_precio_venta = nuevo_precio_costo * factor_margen
    
    print("💰 CÁLCULO DEL NUEVO PRECIO VENTA:")
    print(f"  Factor de margen: {factor_margen:.3f}")
    print(f"  Nuevo precio venta: ${nuevo_precio_costo:.2f} × {factor_margen:.3f} = ${nuevo_precio_venta:.2f}")
    
    print("")
    
    # Resumen final
    print("🎯 RESULTADO FINAL:")
    print(f"  Stock final: {nuevo_stock} unidades")
    print(f"  Precio costo final: ${nuevo_precio_costo:.2f}")
    print(f"  Precio venta final: ${nuevo_precio_venta:.2f}")
    print(f"  Factor de margen mantenido: {factor_margen:.3f}")
    
    # Verificar que el factor se mantiene
    factor_final = nuevo_precio_venta / nuevo_precio_costo
    print(f"  Factor final verificado: {factor_final:.3f}")
    
    if abs(factor_final - factor_margen) < 0.001:
        print("  ✅ PERFECTO: El factor de margen se mantiene")
    else:
        print("  ❌ ERROR: El factor de margen cambió")
    
    print("")
    print("🎉 El sistema debe calcular exactamente estos valores automáticamente!")

if __name__ == "__main__":
    calcular_ejemplo_real()



