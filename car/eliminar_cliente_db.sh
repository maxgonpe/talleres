#!/usr/bin/env bash
set -euo pipefail

# =========================
# Script para eliminar bases de datos de clientes
# =========================

# Configuración
POSTGRES_CONTAINER="postgres_talleres"  # Nombre del contenedor de Postgres
DB_OWNER="maxgonpe"                      # Rol propietario de las BDs

# Función para ejecutar comandos SQL
psql_exec() {
  local db="${2:-postgres}"
  docker exec -i "$POSTGRES_CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DB_OWNER" -d "$db" -c "$1"
}

# Función para verificar si existe una base de datos
db_exists() {
  docker exec -i "$POSTGRES_CONTAINER" psql -U "$DB_OWNER" -d postgres -tA -c \
    "SELECT 1 FROM pg_database WHERE datname = '$1';" | tr -d '[:space:]'
}

# Función para listar todas las conexiones activas a una BD
list_connections() {
  local db_name="$1"
  docker exec -i "$POSTGRES_CONTAINER" psql -U "$DB_OWNER" -d postgres -tA -c \
    "SELECT pid, usename, datname, application_name, state FROM pg_stat_activity WHERE datname = '$db_name';"
}

# Función para terminar conexiones activas
terminate_connections() {
  local db_name="$1"
  echo "🔌 Terminando conexiones activas a '$db_name'..."
  docker exec -i "$POSTGRES_CONTAINER" psql -U "$DB_OWNER" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$db_name' AND pid <> pg_backend_pid();" || true
  sleep 1
}

# Función para eliminar una base de datos
drop_database() {
  local db_name="$1"
  
  echo "=========================================="
  echo "🗑️  Eliminando base de datos: $db_name"
  echo "=========================================="
  
  # Verificar si existe
  if [[ "$(db_exists "$db_name")" != "1" ]]; then
    echo "⚠️  La base de datos '$db_name' no existe."
    return 0
  fi
  
  # Listar conexiones activas
  echo "📊 Verificando conexiones activas..."
  local connections=$(list_connections "$db_name" | wc -l)
  if [[ $connections -gt 0 ]]; then
    echo "⚠️  Hay conexiones activas. Terminándolas..."
    terminate_connections "$db_name"
  else
    echo "✅ No hay conexiones activas."
  fi
  
  # Eliminar la base de datos
  echo "🗑️  Eliminando base de datos '$db_name'..."
  psql_exec "DROP DATABASE IF EXISTS \"$db_name\";" "postgres"
  
  if [[ "$(db_exists "$db_name")" != "1" ]]; then
    echo "✅ Base de datos '$db_name' eliminada exitosamente."
  else
    echo "❌ Error: No se pudo eliminar la base de datos '$db_name'."
    return 1
  fi
  
  echo ""
}

# =========================
# Proceso principal
# =========================

if [[ $# -eq 0 ]]; then
  echo "Uso: $0 <nombre_cliente1> [nombre_cliente2] ..."
  echo "Ejemplo: $0 atlantic stihl"
  echo ""
  echo "Este script eliminará las bases de datos:"
  echo "  - cliente_<nombre_cliente>_db"
  exit 1
fi

echo "=========================================="
echo "🗑️  ELIMINACIÓN DE BASES DE DATOS DE CLIENTES"
echo "=========================================="
echo ""

# Procesar cada cliente
for CLIENT in "$@"; do
  DB_NAME="cliente_${CLIENT}_db"
  drop_database "$DB_NAME"
done

echo "=========================================="
echo "✅ Proceso completado"
echo "=========================================="

