# Arquitectura del Sistema

## Tipo de arquitectura

El sistema utilizará una arquitectura web basada en el patrón
Modelo-Vista-Template de Django.

## Componentes principales

### Presentación
Estará formada por HTML, Bootstrap y JavaScript.

Se encargará de mostrar formularios, botones, mensajes, denuncias y
demás elementos con los que interactuará el usuario.

### Aplicación
Será desarrollada mediante Python y Django.

Se encargará de:
- Procesar solicitudes.
- Validar formularios.
- Aplicar reglas de negocio.
- Gestionar usuarios.
- Registrar denuncias.
- Administrar estados y evidencias.

### Persistencia
Se utilizará PostgreSQL.

Permitirá almacenar:
- Usuarios.
- Categorías.
- Denuncias.
- Evidencias.
- Ubicaciones.
- Estados.

## Comunicación

Usuario
↓
Navegador Web
↓
HTML + Bootstrap + JavaScript
↓
Django / Python
↓
PostgreSQL

## Entorno

Docker será utilizado para mantener separados y configurados los
servicios necesarios para ejecutar Django y PostgreSQL.
