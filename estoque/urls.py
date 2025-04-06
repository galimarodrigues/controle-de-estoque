from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('tabelas/', views.tables, name='tables'),
    path('graficos/', views.charts, name='charts'),
]