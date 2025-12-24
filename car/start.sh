#!/bin/bash
set -e

# Cambiar al directorio de la aplicación
cd /app

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python3 manage.py migrate --noinput

# Recoger archivos estáticos
echo "Recogiendo archivos estáticos..."
python3 manage.py collectstatic --noinput || true

# Ejecutar el comando que viene como argumento (gunicorn)
echo "Iniciando servidor..."
exec "$@"



