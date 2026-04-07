from django.urls import path
from . import views

urlpatterns = [
    path('', views.periodo, name='consulta_index'),
    path('periodo/', views.periodo, name='consulta_periodo'),
]
