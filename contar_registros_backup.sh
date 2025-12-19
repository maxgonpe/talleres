#!/bin/bash
# Script para contar registros en el backup

set -euo pipefail

BACKUP_FILE="/home/max/myproject/cliente_solutioncar_db.sql"

echo "=========================================="
echo "Contando registros en backup"
echo "Backup: $BACKUP_FILE"
echo "=========================================="
echo ""

# Contar trabajos
echo "📋 Trabajos (car_trabajo):"
COPY_LINE=$(grep -n "^COPY public.car_trabajo" "$BACKUP_FILE" | head -1 | cut -d: -f1)

if [[ -n "$COPY_LINE" ]]; then
    # Buscar el final (línea con \.)
    DATA_END=$(sed -n "${COPY_LINE},\$p" "$BACKUP_FILE" | grep -n "^\\\\\." | head -1 | cut -d: -f1)
    
    if [[ -n "$DATA_END" ]]; then
        COUNT=$((DATA_END - 1))
        echo "  ✅ Formato: COPY (PostgreSQL)"
        echo "  ✅ Registros encontrados: $COUNT"
        
        if [[ $COUNT -gt 0 ]]; then
            echo ""
            echo "  Primeros 3 registros (muestra):"
            sed -n "$((COPY_LINE + 1)),$((COPY_LINE + 3))p" "$BACKUP_FILE" | sed 's/^/    /'
        fi
    else
        echo "  ⚠️  No se encontró el final de los datos"
    fi
else
    # Buscar formato INSERT
    INSERT_COUNT=$(grep -c "INSERT INTO public.car_trabajo" "$BACKUP_FILE" 2>/dev/null || echo "0")
    if [[ "$INSERT_COUNT" != "0" ]]; then
        echo "  ✅ Formato: INSERT"
        echo "  ✅ Registros encontrados: $INSERT_COUNT"
        echo ""
        echo "  Primeros 3 registros (muestra):"
        grep "INSERT INTO public.car_trabajo" "$BACKUP_FILE" | head -3 | sed 's/^/    /'
    else
        echo "  ❌ No se encontraron datos de trabajos"
    fi
fi

echo ""
echo ""

# Contar repuestos
echo "📋 Repuestos de trabajo (car_trabajorepuesto):"
COPY_LINE=$(grep -n "^COPY public.car_trabajorepuesto" "$BACKUP_FILE" | head -1 | cut -d: -f1)

if [[ -n "$COPY_LINE" ]]; then
    # Buscar el final (línea con \.)
    DATA_END=$(sed -n "${COPY_LINE},\$p" "$BACKUP_FILE" | grep -n "^\\\\\." | head -1 | cut -d: -f1)
    
    if [[ -n "$DATA_END" ]]; then
        COUNT=$((DATA_END - 1))
        echo "  ✅ Formato: COPY (PostgreSQL)"
        echo "  ✅ Registros encontrados: $COUNT"
        
        if [[ $COUNT -gt 0 ]]; then
            echo ""
            echo "  Primeros 3 registros (muestra):"
            sed -n "$((COPY_LINE + 1)),$((COPY_LINE + 3))p" "$BACKUP_FILE" | sed 's/^/    /'
        fi
    else
        echo "  ⚠️  No se encontró el final de los datos"
    fi
else
    # Buscar formato INSERT
    INSERT_COUNT=$(grep -c "INSERT INTO public.car_trabajorepuesto" "$BACKUP_FILE" 2>/dev/null || echo "0")
    if [[ "$INSERT_COUNT" != "0" ]]; then
        echo "  ✅ Formato: INSERT"
        echo "  ✅ Registros encontrados: $INSERT_COUNT"
        echo ""
        echo "  Primeros 3 registros (muestra):"
        grep "INSERT INTO public.car_trabajorepuesto" "$BACKUP_FILE" | head -3 | sed 's/^/    /'
    else
        echo "  ❌ No se encontraron datos de repuestos"
    fi
fi

echo ""
echo "=========================================="
echo "Resumen:"
echo "=========================================="

# Resumen final
TRABAJO_COUNT="0"
REPUESTO_COUNT="0"

# Contar trabajos
COPY_LINE=$(grep -n "^COPY public.car_trabajo" "$BACKUP_FILE" | head -1 | cut -d: -f1)
if [[ -n "$COPY_LINE" ]]; then
    DATA_END=$(sed -n "${COPY_LINE},\$p" "$BACKUP_FILE" | grep -n "^\\\\\." | head -1 | cut -d: -f1)
    if [[ -n "$DATA_END" ]]; then
        TRABAJO_COUNT=$((DATA_END - 1))
    fi
else
    TRABAJO_COUNT=$(grep -c "INSERT INTO public.car_trabajo" "$BACKUP_FILE" 2>/dev/null || echo "0")
fi

# Contar repuestos
COPY_LINE=$(grep -n "^COPY public.car_trabajorepuesto" "$BACKUP_FILE" | head -1 | cut -d: -f1)
if [[ -n "$COPY_LINE" ]]; then
    DATA_END=$(sed -n "${COPY_LINE},\$p" "$BACKUP_FILE" | grep -n "^\\\\\." | head -1 | cut -d: -f1)
    if [[ -n "$DATA_END" ]]; then
        REPUESTO_COUNT=$((DATA_END - 1))
    fi
else
    REPUESTO_COUNT=$(grep -c "INSERT INTO public.car_trabajorepuesto" "$BACKUP_FILE" 2>/dev/null || echo "0")
fi

echo "  Trabajos: $TRABAJO_COUNT registros"
echo "  Repuestos: $REPUESTO_COUNT registros"
echo ""
echo "=========================================="

