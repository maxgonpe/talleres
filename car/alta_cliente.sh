#!/usr/bin/env bash
set -euo pipefail

# =========================
# Configuración — AJUSTA AQUÍ
# =========================
DOMAIN="netgogo.cl"
NETWORK="traefik_default"
BASE_IMAGE="taller_base:latest"         # Imagen de tu proyecto (con manage.py dentro)
POSTGRES_CONTAINER="postgres_talleres"  # Nombre del contenedor de Postgres
DB_OWNER="maxgonpe"                      # Rol propietario de las BDs
DB_PASSWORD="celsa1961"                  # Password del rol anterior (para Django)
DB_HOST="postgres_talleres"              # Host al que se conectan los contenedores Django
DB_PORT="5432"                           # Puerto de Postgres
SEED_DB="netgogo_talleres"               # Base “semilla” con tablas y datos pre-cargados

# =========================
# Utilidades
# =========================
usage() {
  echo "Uso: $0 <nombre_cliente> [--replace]"
  echo "Ejemplo: $0 pruebados --replace"
}

rand_pass() {
  # genera un password aleatorio (16 chars URL-safe)
  openssl rand -base64 18 | tr -d '\n' | tr '/+' 'Aa' | cut -c1-16
}

psql_exec() {
  # psql en la DB indicada (o postgres si no se pasa) dentro del contenedor
  local db="${2:-postgres}"
  docker exec -i "$POSTGRES_CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DB_OWNER" -d "$db" -c "$1"
}

db_exists() {
  docker exec -i "$POSTGRES_CONTAINER" psql -U "$DB_OWNER" -d postgres -tA -c \
    "SELECT 1 FROM pg_database WHERE datname = '$1';" | tr -d '[:space:]'
}

# =========================
# Entradas
# =========================
CLIENT="${1:-}"
REPLACE="${2:-}"

if [[ -z "$CLIENT" ]]; then
  usage; exit 1
fi

DB_NAME="cliente_${CLIENT}_db"
CONTAINER_NAME="cliente_${CLIENT}"
ADMIN_USER="admin"
ADMIN_EMAIL="admin@${CLIENT}.${DOMAIN}"
ADMIN_PASS="$(rand_pass)"

echo "==> Cliente:            $CLIENT"
echo "==> Base de datos:      $DB_NAME"
echo "==> Contenedor:         $CONTAINER_NAME"
echo "==> Dominio:            https://${CLIENT}.${DOMAIN}/"
echo "==> Semilla desde:      $SEED_DB"
echo

# =========================
# 1) Crear BD del cliente (si no existe)
# =========================
echo "[1/4] Asegurando base de datos $DB_NAME ..."
if [[ "$(db_exists "$DB_NAME")" == "1" ]]; then
  echo "    ℹ️  La BD $DB_NAME ya existe."
else
  psql_exec "CREATE DATABASE ${DB_NAME} OWNER ${DB_OWNER};"
  echo "    ✅ BD $DB_NAME creada."
fi

# =========================
# 2) Copiar esquema + datos desde SEED_DB
# =========================
echo "[2/4] Copiando esquema + datos desde $SEED_DB → $DB_NAME ..."
docker exec -i "$POSTGRES_CONTAINER" bash -lc "\
  pg_dump -U $DB_OWNER -d $SEED_DB -Fc -f /tmp/${DB_NAME}.dump && \
  pg_restore -U $DB_OWNER --no-owner --role=$DB_OWNER -d $DB_NAME /tmp/${DB_NAME}.dump"
echo "    ✅ Copia completada."

# sanity check
docker exec -it "$POSTGRES_CONTAINER" psql -U "$DB_OWNER" -d "$DB_NAME" -c '\dt' >/dev/null
echo "    🔎 Tablas presentes en $DB_NAME (ok)."

# =========================
# 3) (Opcional) Reemplazar contenedor si existe
# =========================
if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
  if [[ "$REPLACE" == "--replace" ]]; then
    echo "[3/4] Eliminando contenedor existente $CONTAINER_NAME ..."
    docker rm -f "$CONTAINER_NAME" >/dev/null
    echo "    ✅ Contenedor anterior eliminado."
  else
    echo "[3/4] ⚠️  Ya existe un contenedor llamado $CONTAINER_NAME."
    echo "     Si quieres reemplazarlo, ejecuta de nuevo con --replace"
    exit 1
  fi
else
  echo "[3/4] No existe contenedor previo. Continuamos."
fi

# =========================
# 4) Lanzar contenedor del cliente
# =========================
echo "[4/4] Lanzando contenedor $CONTAINER_NAME ..."

# Construimos la label de Traefik con backticks sin que bash intente ejecutarlos:
LABEL_RULE='traefik.http.routers.'"${CLIENT}"'.rule=Host(`'"${CLIENT}.${DOMAIN}"'`)'

docker run -d \
  --name "$CONTAINER_NAME" \
  --network "$NETWORK" \
  -e DB_NAME="$DB_NAME" \
  -e DB_USER="$DB_OWNER" \
  -e DB_PASSWORD="$DB_PASSWORD" \
  -e DB_HOST="$DB_HOST" \
  -e DB_PORT="$DB_PORT" \
  -e CLIENT_ADMIN_USERNAME="$ADMIN_USER" \
  -e CLIENT_ADMIN_EMAIL="$ADMIN_EMAIL" \
  -e CLIENT_ADMIN_PASSWORD="$ADMIN_PASS" \
  -l traefik.enable=true \
  -l "$LABEL_RULE" \
  -l "traefik.http.routers.${CLIENT}.entrypoints=websecure" \
  -l "traefik.http.routers.${CLIENT}.tls.certresolver=letsencrypt" \
  -l "traefik.http.services.${CLIENT}.loadbalancer.server.port=8000" \
  "$BASE_IMAGE" >/dev/null

echo "    ✅ Contenedor lanzado."

# =========================
# 5) Verificación rápida de conexión y (por si acaso) creación del admin
#    (si tu imagen ya lo hace en el ENTRYPOINT, esta parte no perjudica)
# =========================

echo "    🔎 Verificando que Django apunta a $DB_NAME ..."
docker exec -it "$CONTAINER_NAME" bash -lc "\
python - <<'PY'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','myproject.settings')
django.setup()
from django.conf import settings
db = settings.DATABASES['default']
print('DB_NAME=', db.get('NAME'))
print('DB_HOST=', db.get('HOST'))
print('DB_USER=', db.get('USER'))
print('DB_PORT=', db.get('PORT'))
PY"

echo "    👤 Asegurando superusuario del cliente ($ADMIN_USER) ..."
docker exec -it "$CONTAINER_NAME" bash -lc "\
python - <<'PY'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','myproject.settings')
django.setup()
from django.contrib.auth import get_user_model
User=get_user_model()
u=os.environ.get('CLIENT_ADMIN_USERNAME','admin')
e=os.environ.get('CLIENT_ADMIN_EMAIL','admin@example.com')
p=os.environ.get('CLIENT_ADMIN_PASSWORD','Admin123')
if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(u,e,p)
    print('    ✅ Superuser creado:', u)
else:
    print('    ℹ️  Superuser ya existe:', u)
PY"

echo
echo "================= RESUMEN ================="
echo "Cliente:        $CLIENT"
echo "URL:            https://${CLIENT}.${DOMAIN}/"
echo "BD del cliente: $DB_NAME"
echo "Contenedor:     $CONTAINER_NAME"
echo "Admin:          ${ADMIN_USER} / ${ADMIN_PASS}"
echo "==========================================="
