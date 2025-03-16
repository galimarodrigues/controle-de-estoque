from django.urls import path
from . import views

app_name = 'estoque'

urlpatterns = [
    path('', views.index, name='index'),
    # path('listar/', views.listar_estoque, name='listar_estoque'),
    # path('adicionar/', views.adicionar_item, name='adicionar_item'),
]