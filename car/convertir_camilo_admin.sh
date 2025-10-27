#!/bin/bash
# convertir_camilo_admin.sh - Convierte a Camilo en administrador en Docker
# Uso: ./convertir_camilo_admin.sh

CONTAINER_NAME="cliente_solutioncar"

echo "👑 Convirtiendo a Camilo en administrador del taller..."

# Verificar que el contenedor existe
if ! docker ps -a --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "❌ Error: El contenedor '$CONTAINER_NAME' no existe"
    echo "   Contenedores disponibles:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

# Verificar que el contenedor está corriendo
if ! docker ps --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "⚠️  El contenedor no está corriendo. Iniciando..."
    docker start $CONTAINER_NAME
    sleep 3
fi

echo "🔧 Ejecutando comandos en el contenedor..."

# Ejecutar comandos Django en el contenedor
docker exec $CONTAINER_NAME python manage.py shell -c "
from django.contrib.auth.models import User
from car.models import Mecanico

print('👥 Buscando usuario camilo...')

try:
    # Buscar a Camilo
    camilo = User.objects.get(username='camilo')
    print(f'✅ Usuario encontrado: {camilo.username}')
    
    # Verificar si ya tiene perfil
    if hasattr(camilo, 'mecanico'):
        # Actualizar a administrador
        camilo.mecanico.rol = 'admin'
        camilo.mecanico.especialidad = 'Propietario del Taller'
        camilo.mecanico.save()
        print(f'✅ {camilo.username} actualizado a ADMINISTRADOR')
    else:
        # Crear perfil de administrador
        mecanico = Mecanico.objects.create(
            user=camilo,
            rol='admin',
            especialidad='Propietario del Taller'
        )
        print(f'✅ Perfil de administrador creado para {camilo.username}')
    
    # Verificar permisos
    print(f'\\n🔐 Permisos de {camilo.username}:')
    print(f'  - Diagnósticos: {camilo.mecanico.puede_ver_diagnosticos}')
    print(f'  - Trabajos: {camilo.mecanico.puede_ver_trabajos}')
    print(f'  - POS: {camilo.mecanico.puede_ver_pos}')
    print(f'  - Compras: {camilo.mecanico.puede_ver_compras}')
    print(f'  - Inventario: {camilo.mecanico.puede_ver_inventario}')
    print(f'  - Administración: {camilo.mecanico.puede_ver_administracion}')
    print(f'  - Gestionar usuarios: {camilo.mecanico.gestionar_usuarios}')
    
    print(f'\\n🎯 Camilo ahora puede entrar como:')
    print(f'   Usuario: {camilo.username}')
    print(f'   Contraseña: [su contraseña actual]')
    print(f'   Rol: {camilo.mecanico.get_rol_display()}')
    
except User.DoesNotExist:
    print('❌ Usuario camilo no encontrado')
    print('👥 Usuarios disponibles:')
    for u in User.objects.all():
        print(f'  - {u.username}')
except Exception as e:
    print(f'❌ Error: {e}')
"

echo ""
echo "✅ ¡Conversión completada!"
echo "👑 Camilo ahora es administrador del taller"
echo ""
echo "🌐 Accede a tu aplicación para ver los cambios:"
echo "   - Login: camilo / [su contraseña]"
echo "   - Verá: Gestión de Usuarios en el panel"
echo "   - Podrá: Crear usuarios, cambiar roles, gestionar permisos"













