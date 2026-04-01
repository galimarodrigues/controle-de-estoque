from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoriaForm, EditCategoriaForm, EditProdutoForm, MovimentacaoForm, ProdutoForm
from .models import Categoria, Movimentacao, Produto, UNIDADES_VALIDAS
from .services import criar_produto_com_estoque_inicial, registrar_movimentacao


def _build_inventory_summary(produtos, movimentacoes=None):
    total_produtos = produtos.count()
    total_itens = sum(produto.quantidade for produto in produtos)
    valor_total = float(sum(produto.quantidade * produto.preco for produto in produtos))
    categorias_ativas = len({produto.categoria_id for produto in produtos})
    resumo = {
        'total_produtos': total_produtos,
        'total_itens': total_itens,
        'valor_total': valor_total,
        'categorias_ativas': categorias_ativas,
    }
    if movimentacoes is not None:
        resumo['total_movimentacoes'] = movimentacoes.count()
    return resumo


def _render_tables(request):
    produtos = Produto.objects.select_related('categoria').all().order_by('nome')
    categorias = Categoria.objects.all().order_by('nome')
    movimentacoes = Movimentacao.objects.select_related('usuario').all()
    return render(request, 'tables.html', {
        'produtos': produtos,
        'categorias': categorias,
        'movimentacoes': movimentacoes,
        'resumo_estoque': _build_inventory_summary(produtos, movimentacoes),
        'unidades_validas': UNIDADES_VALIDAS,
    })


def page_not_found(request, exception):
    return render(request, '404.html', status=404)


def server_error(request):
    return render(request, '500.html', status=500)


def permission_denied(request, exception):
    return render(request, '401.html', status=401)


def index(request):
    categorias = Categoria.objects.all()
    produtos = Produto.objects.all()
    movimentacoes_recentes = Movimentacao.objects.select_related('usuario')[:10]
    resumo_estoque = _build_inventory_summary(produtos, Movimentacao.objects.all())

    category_names = [categoria.nome for categoria in categorias]
    product_quantities = [
        produtos.filter(categoria=categoria).aggregate(Sum('quantidade'))['quantidade__sum'] or 0
        for categoria in categorias
    ]
    stock_values = [
        float(sum(produto.quantidade * produto.preco for produto in produtos.filter(categoria=categoria)))
        for categoria in categorias
    ]

    dados_barras = list(zip(category_names, product_quantities))
    dados_ordenados = sorted(dados_barras, key=lambda x: x[1], reverse=True)
    descricao_barras = [f"{nome_categoria}: {quantidade} unidades" for nome_categoria, quantidade in dados_ordenados]

    dados_pizza = list(zip(category_names, stock_values))
    dados_ordenados_pizza = sorted(dados_pizza, key=lambda x: x[1], reverse=True)
    descricao_pizza = [f"{nome_categoria}: R$ {valor:.2f}" for nome_categoria, valor in dados_ordenados_pizza]

    return render(request, 'base.html', {
        'produtos': produtos,
        'movimentacoes_recentes': movimentacoes_recentes,
        'resumo_estoque': resumo_estoque,
        'categorias': category_names,
        'product_quantities': product_quantities,
        'stock_values': stock_values,
        'descricao_barras': descricao_barras,
        'descricao_pizza': descricao_pizza,
    })


def charts(request):
    categorias = Categoria.objects.all()
    produtos = Produto.objects.all()
    resumo_estoque = _build_inventory_summary(produtos, Movimentacao.objects.all())

    category_names = [categoria.nome for categoria in categorias]
    product_quantities = [
        produtos.filter(categoria=categoria).aggregate(Sum('quantidade'))['quantidade__sum'] or 0
        for categoria in categorias
    ]
    stock_values = [
        float(sum(produto.quantidade * produto.preco for produto in produtos.filter(categoria=categoria)))
        for categoria in categorias
    ]

    dados_barras = list(zip(category_names, product_quantities))
    dados_ordenados = sorted(dados_barras, key=lambda x: x[1], reverse=True)
    descricao_barras = [f"{nome_categoria}: {quantidade} unidades" for nome_categoria, quantidade in dados_ordenados]

    dados_pizza = list(zip(category_names, stock_values))
    dados_ordenados_pizza = sorted(dados_pizza, key=lambda x: x[1], reverse=True)
    descricao_pizza = [f"{nome_categoria}: R$ {valor:.2f}" for nome_categoria, valor in dados_ordenados_pizza]

    return render(request, 'charts.html', {
        'resumo_estoque': resumo_estoque,
        'categorias': category_names,
        'product_quantities': product_quantities,
        'stock_values': stock_values,
        'descricao_barras': descricao_barras,
        'descricao_pizza': descricao_pizza,
    })


def tables(request):
    return _render_tables(request)


def add_categoria(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria cadastrada com sucesso.')
        else:
            messages.error(request, '; '.join(
                erro for erros in form.errors.values() for erro in erros
            ))
    return redirect('tables')


def add_produto(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            criar_produto_com_estoque_inicial(
                nome=form.cleaned_data['nome'],
                categoria=form.cleaned_data['categoria'],
                preco=form.cleaned_data['preco'],
                unidade=form.cleaned_data['unidade'],
                quantidade_inicial=form.cleaned_data.get('quantidade_inicial') or 0,
                usuario=request.user,
                motivo=form.cleaned_data.get('motivo') or 'Estoque inicial',
                fornecedor=form.cleaned_data.get('fornecedor') or '',
                observacao=form.cleaned_data.get('observacao') or '',
            )
            messages.success(request, 'Produto cadastrado e estoque inicial registrado.')
        else:
            messages.error(request, '; '.join(
                erro for erros in form.errors.values() for erro in erros
            ))
    return redirect('tables')


def entrada_produto(request):
    if request.method == 'POST':
        form = MovimentacaoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    registrar_movimentacao(
                        produto_id=form.cleaned_data['produto'].id,
                        tipo='entrada',
                        quantidade=form.cleaned_data['quantidade'],
                        usuario=request.user,
                        custo_unitario=form.cleaned_data.get('custo_unitario'),
                        motivo=form.cleaned_data.get('motivo') or 'Reposicao de estoque',
                        fornecedor=form.cleaned_data.get('fornecedor') or '',
                        observacao=form.cleaned_data.get('observacao') or '',
                    )
            except ValueError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, 'Entrada de estoque registrada com sucesso.')
        else:
            messages.error(request, '; '.join(
                erro for erros in form.errors.values() for erro in erros
            ))
    return redirect('tables')


def remover_produto(request):
    if request.method == 'POST':
        remover_tudo = request.POST.get('remover_tudo') == 'on'
        if remover_tudo:
            produto = get_object_or_404(Produto, id=request.POST.get('produto'))
            if produto.quantidade > 0:
                messages.error(
                    request,
                    'Nao e permitido excluir produto com estoque disponivel. Zere o estoque com movimentacoes de saida primeiro.'
                )
            else:
                produto.delete()
                messages.success(request, 'Produto excluido sem remover o historico de movimentacoes.')
            return redirect('tables')

        form = MovimentacaoForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    registrar_movimentacao(
                        produto_id=form.cleaned_data['produto'].id,
                        tipo='saida',
                        quantidade=form.cleaned_data['quantidade'],
                        usuario=request.user,
                        custo_unitario=form.cleaned_data.get('custo_unitario'),
                        motivo=form.cleaned_data.get('motivo') or 'Consumo/saida de estoque',
                        fornecedor=form.cleaned_data.get('fornecedor') or '',
                        observacao=form.cleaned_data.get('observacao') or '',
                    )
            except ValueError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, 'Saida de estoque registrada com sucesso.')
        else:
            messages.error(request, '; '.join(
                erro for erros in form.errors.values() for erro in erros
            ))

    return redirect('tables')


def remover_categoria(request):
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria')
        Categoria.objects.filter(id=categoria_id).delete()
        messages.success(request, 'Categoria removida com sucesso.')
    return redirect('tables')


def editar_categoria(request):
    if request.method == 'POST':
        categoria = get_object_or_404(Categoria, id=request.POST.get('categoria'))
        form = EditCategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria atualizada com sucesso.')
        else:
            messages.error(request, '; '.join(
                erro for erros in form.errors.values() for erro in erros
            ))
    return redirect('tables')


def editar_produto(request):
    if request.method == 'POST':
        produto = get_object_or_404(Produto, id=request.POST.get('produto'))
        form = EditProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto atualizado sem alterar o historico de movimentacoes.')
        else:
            messages.error(request, '; '.join(
                erro for erros in form.errors.values() for erro in erros
            ))
    return redirect('tables')
