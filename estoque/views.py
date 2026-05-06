import json
import subprocess
from datetime import timedelta

from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .forms import CategoriaForm, EditCategoriaForm, EditProdutoForm, MovimentacaoForm, ProdutoForm
from .models import Categoria, Movimentacao, Produto, UNIDADES_VALIDAS
from .seed_runner import HARDCODED_SEED_API_KEY, get_supported_seed_names, run_seed
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

    trinta_dias_atras = timezone.now() - timedelta(days=30)
    saidas_30dias = Movimentacao.objects.filter(
        data__gte=trinta_dias_atras,
        tipo='saida',
        produto__isnull=False
    ).values('produto').annotate(total_saida=Sum('quantidade'))

    saida_por_produto = {
        item['produto']: item['total_saida'] or 0
        for item in saidas_30dias
    }

    produtos_estoque = []
    produtos_com_estoque = Produto.objects.filter(quantidade__gt=0).order_by('nome')
    for produto in produtos_com_estoque:
        estoque_atual = produto.quantidade
        saida_quantidade = saida_por_produto.get(produto.id, 0)
        consumo_diario = round(saida_quantidade / 30, 2)
        giro_30dias = round(saida_quantidade / estoque_atual, 2) if estoque_atual else 0
        produtos_estoque.append({
            'nome': produto.nome,
            'estoque': estoque_atual,
            'consumo_diario': consumo_diario,
            'giro_30dias': giro_30dias,
        })

    # Produtos mais vendidos (top 5)
    produtos_mais_vendidos = sorted(
        [(item['produto'], item['total_saida']) for item in saidas_30dias],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    produtos_mais_vendidos = [
        {'produto': Produto.objects.get(id=produto_id).nome, 'vendas': vendas}
        for produto_id, vendas in produtos_mais_vendidos
    ]

    # Produtos menos vendidos (bottom 5)
    produtos_menos_vendidos = sorted(
        [(item['produto'], item['total_saida']) for item in saidas_30dias],
        key=lambda x: x[1]
    )[:5]
    produtos_menos_vendidos = [
        {'produto': Produto.objects.get(id=produto_id).nome, 'vendas': vendas}
        for produto_id, vendas in produtos_menos_vendidos
    ]

    # Produtos com baixo estoque (< 30% do estoque médio histórico)
    produtos_baixo_estoque = []
    for produto in Produto.objects.all():
        # Calcular estoque médio histórico baseado nas entradas
        entradas = Movimentacao.objects.filter(
            produto=produto,
            tipo='entrada'
        ).aggregate(total_quantidade=Sum('quantidade'), count=Count('id'))
        
        if entradas['count'] and entradas['count'] > 0:
            estoque_medio_historico = entradas['total_quantidade'] / entradas['count']
            limite_baixo_estoque = estoque_medio_historico * 0.3
            
            if produto.quantidade < limite_baixo_estoque:
                produtos_baixo_estoque.append({
                    'nome': produto.nome,
                    'quantidade': produto.quantidade,
                    'estoque_medio': round(estoque_medio_historico, 2),
                    'limite': round(limite_baixo_estoque, 2)
                })
    
    # Ordenar por quantidade (menor primeiro)
    produtos_baixo_estoque.sort(key=lambda x: x['quantidade'])

    return render(request, 'charts.html', {
        'resumo_estoque': resumo_estoque,
        'categorias': category_names,
        'product_quantities': product_quantities,
        'stock_values': stock_values,
        'descricao_barras': descricao_barras,
        'descricao_pizza': descricao_pizza,
        'produtos_estoque': produtos_estoque,
        'produtos_mais_vendidos': produtos_mais_vendidos,
        'produtos_menos_vendidos': produtos_menos_vendidos,
        'produtos_baixo_estoque': produtos_baixo_estoque,
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


def _parse_seed_request_payload(request):
    if request.content_type and 'application/json' in request.content_type:
        try:
            return json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError as exc:
            raise ValueError(f'JSON invalido: {exc.msg}')
    return {
        'seed_name': request.POST.get('seed_name'),
        'mode': request.POST.get('mode'),
        'dry_run': request.POST.get('dry_run'),
        'force_sqlite': request.POST.get('force_sqlite'),
    }


def _as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


@csrf_exempt
def run_seed_api(request):
    if request.method != 'POST':
        return JsonResponse(
            {
                'detail': 'Metodo nao permitido. Use POST.',
                'supported_seeds': get_supported_seed_names(),
            },
            status=405,
        )

    provided_key = request.headers.get('X-API-Key') or request.POST.get('api_key')
    if provided_key != HARDCODED_SEED_API_KEY:
        return JsonResponse({'detail': 'API key invalida.'}, status=403)

    try:
        payload = _parse_seed_request_payload(request)
    except ValueError as exc:
        return JsonResponse({'detail': str(exc)}, status=400)

    seed_name = payload.get('seed_name') or 'seed_prod_v2'
    mode = payload.get('mode') or 'orm'
    dry_run = _as_bool(payload.get('dry_run'))
    force_sqlite = _as_bool(payload.get('force_sqlite'), default=(mode == 'orm'))

    try:
        completed = run_seed(
            seed_name=seed_name,
            mode=mode,
            dry_run=dry_run,
            force_sqlite=force_sqlite,
        )
    except ValueError as exc:
        return JsonResponse(
            {
                'detail': str(exc),
                'supported_seeds': get_supported_seed_names(),
            },
            status=400,
        )
    except subprocess.TimeoutExpired:
        return JsonResponse(
            {
                'detail': 'A execucao do seed excedeu o tempo limite.',
                'seed_name': seed_name,
                'mode': mode,
            },
            status=504,
        )

    status_code = 200 if completed.returncode == 0 else 500
    return JsonResponse(
        {
            'ok': completed.returncode == 0,
            'seed_name': seed_name,
            'mode': mode,
            'dry_run': dry_run,
            'force_sqlite': force_sqlite,
            'returncode': completed.returncode,
            'stdout': completed.stdout,
            'stderr': completed.stderr,
            'supported_seeds': get_supported_seed_names(),
        },
        status=status_code,
    )
