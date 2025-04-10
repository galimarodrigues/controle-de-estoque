from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('tabelas/', views.tables, name='tables'),
    path('graficos/', views.charts, name='charts'),
    path('add_categoria/', views.add_categoria, name='add_categoria'),
    path('add_produto/', views.add_produto, name='add_produto'),
    path('remover_produto/', views.remover_produto, name='remover_produto'),
    path('remover_categoria/', views.remover_categoria, name='remover_categoria'),
    path('editar_categoria/', views.editar_categoria, name='editar_categoria'),
    path('editar_produto/', views.editar_produto, name='editar_produto'),
]