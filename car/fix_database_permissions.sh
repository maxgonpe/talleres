#!/bin/bash

DB_NAME="cliente_solutioncar_db"
DB_USER="maxgonpe"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✅ $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $1${NC}"
}

echo "============================================================================="
echo "🔧 REPARANDO PERMISOS DE BASE DE DATOS"
echo "============================================================================="

# 1. Otorgar permisos como postgres
log "Otorgando permisos al usuario $DB_USER..."

sudo -u postgres psql -c "
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
GRANT ALL PRIVILEGES ON SCHEMA public TO $DB_USER;
GRANT CREATE ON SCHEMA public TO $DB_USER;
ALTER USER $DB_USER CREATEDB;
"

if [ $? -eq 0 ]; then
    log_success "Permisos otorgados correctamente"
else
    log_error "Error al otorgar permisos"
    exit 1
fi

# 2. Verificar permisos
log "Verificando permisos..."
sudo -u postgres psql -d $DB_NAME -c "
SELECT 
    schemaname,
    tablename,
    tableowner,
    hasinserts,
    hasselects,
    hasupdates,
    hasdeletes
FROM pg_tables 
WHERE schemaname = 'public'
LIMIT 5;
"

# 3. Probar conexión con el usuario
log "Probando conexión con usuario $DB_USER..."
sudo -u postgres psql -d $DB_NAME -U $DB_USER -c "SELECT current_user, current_database();"

log_success "Permisos reparados correctamente"
echo "============================================================================="
