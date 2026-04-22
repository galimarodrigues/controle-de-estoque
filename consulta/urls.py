from django.urls import path
from . import views

urlpatterns = [
    path('', views.periodo, name='consulta_index'),
    path('periodo/', views.periodo, name='consulta_periodo'),
    path('categoria/', views.consulta_categoria, name='consulta_categoria'),
    path('produto/', views.consulta_produto, name='consulta_produto'),
    path('historico/', views.historico_vendas, name='historico_vendas'),
]
