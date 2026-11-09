from django.urls import path
from . import views

app_name = "denuncias"
urlpatterns = [
    path("", views.listado, name="listado"),
    path("nueva/", views.nueva, name="nueva"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/gestionar/", views.gestionar, name="gestionar"),
]
