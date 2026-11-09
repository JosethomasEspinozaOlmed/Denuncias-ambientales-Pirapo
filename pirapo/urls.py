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
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
