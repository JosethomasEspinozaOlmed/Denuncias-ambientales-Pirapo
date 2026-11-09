# Sistema web de denuncias ambientales — Pirapó

Primera versión funcional del prototipo académico para el municipio de Pirapó.

## Tecnologías

- Python 3.13 y Django 5.2 LTS
- PostgreSQL 17
- Bootstrap 5 y JavaScript
- Docker Compose
- Leaflet/OpenStreetMap (visualización del mapa; necesita conexión a Internet)

## Iniciar en Windows (PowerShell + Docker Desktop)

1. Descomprimir esta carpeta en un directorio de proyectos (ej. `C:\Proyectos\sistema_denuncias_pirapo`).
2. Abrir la carpeta completa en Visual Studio Code.
3. Verificar que Docker Desktop esté **abierto y en funcionamiento**.
4. Abrir una terminal PowerShell dentro de la carpeta del proyecto y ejecutar:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose logs -f web
```

El contenedor crea las migraciones del prototipo y ejecuta las migraciones de PostgreSQL al arrancar. En la salida se debe ver `Starting development server at http://0.0.0.0:8000/`. Detener los logs con `Ctrl+C` (la app continuará ejecutándose).

5. En una terminal PowerShell nueva, cargar categorías y crear administrador:

```powershell
docker compose exec web python manage.py cargar_categorias
docker compose exec web python manage.py createsuperuser
```

6. Abrir **http://127.0.0.1:8000/**.

**Importante:** `createsuperuser` solicita nombre de usuario, correo y contraseña; la contraseña no se muestra al escribirla. Para iniciar sesión como administrador, ingresar con ese usuario en `/ingresar/` o en `/admin/`.

## Cómo probar los tres roles

1. **Ciudadano:** abrir `/registro/`, crear una cuenta e iniciar sesión. Registrar una denuncia ambiental con categoría, descripción y ubicación (foto opcional).
2. **Administrador:** iniciar sesión con la cuenta creada con `createsuperuser` y entrar en `/admin/`. Desde **Usuarios** crear otro usuario seleccionando el rol **Funcionario municipal**. En **Categorías** se pueden gestionar las categorías.
3. **Funcionario:** cerrar sesión e iniciar con el usuario funcionario. Abrir `Denuncias` → `Detalle` → `Gestionar denuncia`, asignar a un funcionario y actualizar el estado.

Las cuentas creadas desde `/registro/` siempre son ciudadanas, incluso si alguien intenta enviar manualmente un rol distinto.

## Comandos útiles

```powershell
# Ver estado de los contenedores
docker compose ps

# Revisar errores
docker compose logs -f web

# Ejecutar pruebas automatizadas
docker compose exec web python manage.py test

# Detener servicios sin borrar datos
docker compose down

# Reiniciar servicios
docker compose up -d
```

No usar `docker compose down -v` si se quieren conservar los datos, porque `-v` borra el volumen de PostgreSQL.

## Prueba desde otro teléfono por Wi-Fi

1. PC y teléfono deben estar conectados a la misma red Wi-Fi.
2. En PowerShell de Windows ejecutar `ipconfig` y anotar la **IPv4 de la PC** (por ejemplo `192.168.0.10`).
3. Editar `.env` y agregar esa IP en `DJANGO_ALLOWED_HOSTS`, sin espacios (ejemplo `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.0.10`).
4. Reiniciar el contenedor para tomar la configuración: `docker compose up -d --force-recreate web`.
5. Abrir en el teléfono `http://IP_DE_LA_PC:8000/`, sustituyendo por la IP real.
6. Si Windows Firewall solicita permiso, permitir conexiones **solo en redes privadas**.

> La geolocalización automática del navegador suele requerir HTTPS al acceder mediante una IP LAN. Para la primera prueba móvil se puede completar la ubicación manualmente. No abrir este servidor de desarrollo directamente a Internet.

## Reglas ya implementadas

- Tres roles: Ciudadano, Funcionario municipal y Administrador.
- El registro público solo crea ciudadanos.
- Ciudadanos solo pueden consultar sus denuncias.
- Denuncia: categoría, descripción y ubicación obligatorias; foto opcional (JPG/PNG/WebP, 5 MB máx.).
- Ubicación por texto o coordenadas del mapa.
- Estado inicial `Pendiente`; estados posibles `Pendiente`, `En proceso`, `Resuelto`.
- Solo funcionario autorizado asigna la denuncia o cambia el estado.
- Se registra el historial básico de creación, asignación y cambio de estado.
- El administrador gestiona usuarios y categorías por Django Admin y puede consultar denuncias.

## Estado de la entrega

**Es un prototipo de desarrollo local**, no una aplicación lista para uso público. Faltan pantallas finales según el mockup, estadísticas, reportes imprimibles, filtros avanzados, seguridad para despliegue y pruebas reales con usuarios. Los accesos `/admin/` y `/ingresar/` son para el prototipo.

**La carpeta `usuarios/migrations/` y `denuncias/migrations/` se completará automáticamente al iniciar Docker.** Conservar esos archivos generados en el repositorio Git. Si el modelo cambia más adelante, se ejecutará `makemigrations` y `migrate`.

No se incluyen datos personales reales, cuentas precargadas ni contraseñas institucionales.
