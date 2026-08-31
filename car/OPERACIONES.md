# Operación y despliegue

## Variables requeridas en producción

```text
DJANGO_SECRET_KEY=<secreto-largo-y-aleatorio>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=netgogo.cl,www.netgogo.cl
DJANGO_LOG_LEVEL=INFO
OPENAI_API_KEY=<clave-si-se-usa-IA>
VEHICLE_LOOKUP_API_KEY=<clave-si-se-habilita-la-consulta-por-placa>
```

Para PostgreSQL también se configuran `DB_ENGINE`, `DB_NAME`, `DB_USER`,
`DB_PASSWORD`, `DB_HOST` y `DB_PORT`.

## Despliegue

```bash
../env/bin/python manage.py migrate
../env/bin/python manage.py collectstatic --noinput
../env/bin/python manage.py check --deploy
../env/bin/python manage.py test car.tests -v 1
gunicorn myproject.wsgi:application
```

## Backups

Crear un backup de base de datos y media:

```bash
./scripts/backup.sh
```

Verificar un backup antes de restaurarlo:

```bash
./scripts/verify_backup.sh backups/talleres-FECHA.tar.gz
```

El backup contiene un checksum externo y un manifiesto interno. Los backups
deben almacenarse fuera del servidor y probarse periódicamente en un entorno
aislado.

## CI

El workflow `.github/workflows/django.yml` valida migraciones, configuración,
compilación y pruebas en cada cambio.

## Consulta de vehículos por placa

El flujo existente se conserva. Cuando el proveedor vuelva a estar disponible,
configurar `VEHICLE_LOOKUP_API_KEY` sin modificar el contrato de la interfaz.
