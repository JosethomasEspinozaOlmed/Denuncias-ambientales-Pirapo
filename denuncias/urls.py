from django.urls import path
from . import views

app_name = 'denuncias'
urlpatterns = [
    path('', views.listado, name='listado'),
    path('nueva/', views.nueva, name='nueva'),
    path('exportar/csv/', views.exportar_csv, name='exportar_csv'),
    path('<int:pk>/', views.detalle, name='detalle'),
    path('<int:pk>/gestionar/', views.gestionar, name='gestionar'),
    path('<int:pk>/verificacion/nueva/', views.registrar_actuacion, name='registrar_actuacion'),
]
