# Instrucciones para Resolver el Error "Bad Gateway"

## Problema Identificado
El contenedor `postgres_talleres` está detenido, causando que todos los contenedores Django de clientes no puedan conectarse a la base de datos, resultando en errores "Bad Gateway".

## Solución Rápida

### Opción 1: Usar el script completo de diagnóstico (Recomendado)
```bash
# En el servidor de producción (/home/max/myproject)
./diagnosticar_postgres.sh
```

Este script:
- Verifica el estado del contenedor PostgreSQL
- Muestra los logs para entender por qué se detuvo
- Intenta reiniciar el contenedor automáticamente
- Verifica la conectividad

### Opción 2: Pasos manuales

#### 1. Verificar estado y logs
```bash
docker ps -a | grep postgres_talleres
docker logs --tail 50 postgres_talleres
```

#### 2. Reiniciar PostgreSQL
```bash
docker start postgres_talleres
```

#### 3. Verificar que PostgreSQL esté listo
```bash
# Esperar unos segundos después del start
docker exec postgres_talleres pg_isready -U maxgonpe
```

#### 4. Verificar conectividad desde contenedores Django
```bash
./verificar_conectividad.sh
```

#### 5. Verificar logs de Django
```bash
./verificar_logs_django.sh
```

## Scripts Disponibles

1. **diagnosticar_postgres.sh** - Diagnóstico completo y reinicio automático
2. **reiniciar_postgres.sh** - Solo reinicia PostgreSQL y verifica que esté listo
3. **verificar_conectividad.sh** - Verifica conectividad desde todos los contenedores de clientes
4. **verificar_logs_django.sh** - Revisa logs de todos los contenedores Django buscando errores

## Comandos Útiles Adicionales

### Ver estado de todos los contenedores
```bash
docker ps -a
```

### Ver logs en tiempo real de un contenedor
```bash
docker logs -f postgres_talleres
docker logs -f cliente_solutioncar
```

### Verificar variables de entorno de BD en un contenedor
```bash
docker exec cliente_solutioncar env | grep -E "^DB_|^DATABASE"
```

### Verificar que Django puede conectarse a la BD
```bash
docker exec cliente_solutioncar python manage.py check --database default
```

## Si el Reinicio Falla

Si `docker start postgres_talleres` falla:

1. **Ver logs detallados:**
   ```bash
   docker logs postgres_talleres
   ```

2. **Ver información del contenedor:**
   ```bash
   docker inspect postgres_talleres
   ```

3. **Verificar espacio en disco:**
   ```bash
   df -h
   docker system df
   ```

4. **Verificar recursos del sistema:**
   ```bash
   free -h
   docker stats --no-stream
   ```

5. **Si es necesario, recrear el contenedor:**
   - Verificar si hay un docker-compose.yml o script de creación
   - Verificar volúmenes de datos persistentes
   - Hacer backup antes de recrear

## Verificación Final

Después de reiniciar PostgreSQL, verifica que:

1. ✅ El contenedor está corriendo: `docker ps | grep postgres_talleres`
2. ✅ PostgreSQL responde: `docker exec postgres_talleres pg_isready -U maxgonpe`
3. ✅ Los contenedores Django pueden conectarse: `./verificar_conectividad.sh`
4. ✅ No hay errores en los logs: `./verificar_logs_django.sh`
5. ✅ El sitio web funciona correctamente (probar en el navegador)

## Notas

- El contenedor `postgres_talleres` debe estar en la misma red Docker que los contenedores de clientes
- Los contenedores de clientes usan variables de entorno para conectarse a PostgreSQL
- Si el problema persiste después del reinicio, puede ser necesario investigar por qué se detuvo (falta de recursos, error en la BD, etc.)
