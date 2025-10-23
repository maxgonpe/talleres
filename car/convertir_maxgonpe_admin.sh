#!/bin/bash
# convertir_maxgonpe_admin.sh - Convierte a maxgonpe en administrador en Docker
# Uso: ./convertir_maxgonpe_admin.sh

CONTAINER_NAME="cliente_solutioncar"

echo "👑 Convirtiendo a maxgonpe en administrador del taller..."

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

print('👥 Buscando usuario maxgonpe...')

try:
    # Buscar a maxgonpe
    maxgonpe = User.objects.get(username='maxgonpe')
    print(f'✅ Usuario encontrado: {maxgonpe.username}')
    
    # Verificar si ya tiene perfil
    if hasattr(maxgonpe, 'mecanico'):
        # Actualizar a administrador
        maxgonpe.mecanico.rol = 'admin'
        maxgonpe.mecanico.especialidad = 'Administrador del Sistema'
        maxgonpe.mecanico.save()
        print(f'✅ {maxgonpe.username} actualizado a ADMINISTRADOR')
    else:
        # Crear perfil de administrador
        mecanico = Mecanico.objects.create(
            user=maxgonpe,
            rol='admin',
            especialidad='Administrador del Sistema'
        )
        print(f'✅ Perfil de administrador creado para {maxgonpe.username}')
    
    # Verificar permisos
    print(f'\\n🔐 Permisos de {maxgonpe.username}:')
    print(f'  - Diagnósticos: {maxgonpe.mecanico.puede_ver_diagnosticos}')
    print(f'  - Trabajos: {maxgonpe.mecanico.puede_ver_trabajos}')
    print(f'  - POS: {maxgonpe.mecanico.puede_ver_pos}')
    print(f'  - Compras: {maxgonpe.mecanico.puede_ver_compras}')
    print(f'  - Inventario: {maxgonpe.mecanico.puede_ver_inventario}')
    print(f'  - Administración: {maxgonpe.mecanico.puede_ver_administracion}')
    print(f'  - Gestionar usuarios: {maxgonpe.mecanico.gestionar_usuarios}')
    
    print(f'\\n🎯 maxgonpe ahora puede entrar como:')
    print(f'   Usuario: {maxgonpe.username}')
    print(f'   Contraseña: celsa')
    print(f'   Rol: {maxgonpe.mecanico.get_rol_display()}')
    
    # También verificar si camilo existe y mostrar su estado
    try:
        camilo = User.objects.get(username='camilo')
        if hasattr(camilo, 'mecanico'):
            print(f'\\n👤 Estado de Camilo:')
            print(f'   Usuario: {camilo.username}')
            print(f'   Rol: {camilo.mecanico.get_rol_display()}')
            print(f'   Admin: {camilo.mecanico.puede_ver_administracion}')
        else:
            print(f'\\n👤 Camilo no tiene perfil de mecánico')
    except User.DoesNotExist:
        print(f'\\n👤 Usuario camilo no encontrado')
    
except User.DoesNotExist:
    print('❌ Usuario maxgonpe no encontrado')
    print('👥 Usuarios disponibles:')
    for u in User.objects.all():
        print(f'  - {u.username}')
except Exception as e:
    print(f'❌ Error: {e}')
"

echo ""
echo "✅ ¡Conversión completada!"
echo "👑 maxgonpe ahora es administrador del taller"
echo ""
echo "🌐 Accede a tu aplicación para ver los cambios:"
echo "   - Login: maxgonpe / celsa"
echo "   - Verás: Gestión de Usuarios en el panel"
echo "   - Podrás: Crear usuarios, cambiar roles, gestionar permisos"
echo "   - Podrás: Autorizar a Camilo como administrador"








