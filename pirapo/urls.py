from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from usuarios import views as usuarios_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", usuarios_views.inicio, name="inicio"),
    path("registro/", usuarios_views.registro, name="registro"),
    path("ingresar/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("panel/", usuarios_views.dashboard, name="dashboard"),
    path("denuncias/", include("denuncias.urls")),
    path("gestion/", include("usuarios.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

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
