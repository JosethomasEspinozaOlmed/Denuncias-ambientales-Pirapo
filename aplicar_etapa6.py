# Añade sólo los ajustes de correo a settings.py y urls.py, con copias .bak.
from pathlib import Path

ROOT = Path(__file__).resolve().parent
settings = ROOT / 'pirapo' / 'settings.py'
urls = ROOT / 'pirapo' / 'urls.py'
for archivo in (settings, urls):
    if not archivo.is_file():
        raise SystemExit(f'Falta {archivo}. Ejecutar desde la carpeta del proyecto Django.')

ajustes = '''
# Etapa 6: correo para acceso, manteniendo usuarios existentes y Django Admin.
AUTHENTICATION_BACKENDS = ['usuarios.backends.CorreoOUsuarioBackend']
DEFAULT_FROM_EMAIL = os.getenv('DJANGO_DEFAULT_FROM_EMAIL', 'Pirapo Ambiental <no-reply@pirapo.local>')
EMAIL_BACKEND = os.getenv(
    'DJANGO_EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.getenv('DJANGO_EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('DJANGO_EMAIL_PORT', '25'))
EMAIL_HOST_USER = os.getenv('DJANGO_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('DJANGO_EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('DJANGO_EMAIL_USE_TLS', 'False').lower() == 'true'
PASSWORD_RESET_TIMEOUT = 3600
'''
rutas = '''
# Etapa 6: recuperación de contraseña (correo real solo con SMTP configurado).
from django.contrib.auth import views as vistas_correo
urlpatterns += [
    path('recuperar-clave/', vistas_correo.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
    ), name='password_reset'),
    path('recuperar-clave/enviado/', vistas_correo.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password_reset_done'),
    path('restablecer-clave/<uidb64>/<token>/', vistas_correo.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('restablecer-clave/finalizado/', vistas_correo.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),
]
'''

def modificar(ruta, marcador, bloque):
    contenido = ruta.read_text(encoding='utf-8')
    if marcador in contenido:
        print(f'Ya configurado: {ruta.name} (sin modificar)')
        return
    backup = ROOT / 'respaldo_etapa6' / (ruta.name + '.bak')
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        backup.write_text(contenido, encoding='utf-8')
    ruta.write_text(contenido.rstrip() + '\n\n' + bloque.strip() + '\n', encoding='utf-8')
    print(f'Actualizado: {ruta} | respaldo: {backup}')

modificar(settings, "'usuarios.backends.CorreoOUsuarioBackend'", ajustes)
modificar(urls, "name='password_reset'", rutas)
print('Listo. Ejecutá: docker compose exec web python manage.py check')
