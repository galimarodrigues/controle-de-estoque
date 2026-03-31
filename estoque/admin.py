from django.contrib import admin

from .models import Categoria, Movimentacao, Produto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'quantidade', 'unidade', 'preco')
    list_filter = ('categoria', 'unidade')
    search_fields = ('nome',)


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('produto_nome', 'tipo', 'quantidade', 'unidade', 'custo_unitario', 'fornecedor', 'data')
    list_filter = ('tipo', 'categoria_nome', 'unidade', 'data')
    search_fields = ('produto_nome', 'fornecedor', 'motivo', 'observacao')
