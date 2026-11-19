from django.urls import path
from . import admin_views as views

app_name = 'administracion'

urlpatterns = [
    path('', views.panel, name='panel'),
    path('usuarios/', views.usuarios_listado, name='usuarios'),
    path('usuarios/nuevo/', views.usuario_nuevo, name='usuario_nuevo'),
    path('usuarios/<int:pk>/editar/', views.usuario_editar, name='usuario_editar'),
    path('usuarios/<int:pk>/clave/', views.usuario_clave, name='usuario_clave'),
    path('usuarios/<int:pk>/estado/', views.usuario_estado, name='usuario_estado'),
    path('categorias/', views.categorias_listado, name='categorias'),
    path('categorias/nueva/', views.categoria_nueva, name='categoria_nueva'),
    path('categorias/<int:pk>/editar/', views.categoria_editar, name='categoria_editar'),
    path('categorias/<int:pk>/estado/', views.categoria_estado, name='categoria_estado'),
]
