from datetime import datetime, timedelta

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import F, FloatField, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone

from estoque.models import Categoria, Movimentacao, Produto
from .forms import PeriodoConsultaForm


def montar_query_string(request):
    parametros = request.GET.copy()
    parametros.pop('page', None)
    query_string = parametros.urlencode()
    return f"&{query_string}" if query_string else ""


def paginar(request, queryset, itens_por_pagina=50):
    # Funcao para regular o numero de itens exibidos por página
    paginator = Paginator(queryset, itens_por_pagina)
    pagina = request.GET.get('page', 1)

    try:
        return paginator.page(pagina)
    
    except PageNotAnInteger:
        return paginator.page(1)
    
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def valor_por_movimentacao():
    return F('quantidade') * Coalesce(
        'custo_unitario',
        F('produto__preco'),
        output_field=FloatField(),
    )


def total_por_tipo(movimentacoes, tipo_movimentacao):
    return movimentacoes.filter(tipo=tipo_movimentacao).aggregate(
        total=Coalesce(Sum(valor_por_movimentacao()), 0, output_field=FloatField())
    )['total'] or 0


def periodo(request):
    """View para filtrar todas as movimentações dentro de um intervalo de tempo escolhido"""
    form = PeriodoConsultaForm(request.GET or None)
    inicio_periodo = timezone.now() - timedelta(days=7) #padrao definido para os ultimo 7 dias
    fim_periodo = timezone.now()

    if form.is_valid():
        dados_limpos = form.cleaned_data
        inicio_periodo = timezone.make_aware(datetime.combine(dados_limpos['data_inicio'], datetime.min.time()))
        fim_periodo = timezone.make_aware(datetime.combine(dados_limpos['data_fim'], datetime.max.time()))

    movimentacoes = Movimentacao.objects.filter(data__range=(inicio_periodo, fim_periodo))
    contagem_entradas = movimentacoes.filter(tipo='entrada').count()
    contagem_saidas = movimentacoes.filter(tipo='saida').count()
    movimentacoes_pagina = paginar(request, movimentacoes.order_by('data'))
    query_string = montar_query_string(request)

    total_arrecadado = total_por_tipo(movimentacoes, 'saida')
    total_custos = total_por_tipo(movimentacoes, 'entrada')

    top_produtos = movimentacoes.filter(tipo='saida').values('produto__nome').annotate(
        total_vendas=Coalesce(Sum(valor_por_movimentacao()), 0, output_field=FloatField())
    ).order_by('-total_vendas')[:5]

    top_categorias = movimentacoes.filter(tipo='saida').values('produto__categoria__nome').annotate(
        total_vendas=Coalesce(Sum(valor_por_movimentacao()), 0, output_field=FloatField())
    ).order_by('-total_vendas')[:5]

    contexto = {
        'form': form,
        'movimentacoes_periodo': movimentacoes_pagina,
        'page_obj': movimentacoes_pagina,
        'query_string': query_string,
        'contagem_entradas': contagem_entradas,
        'contagem_saidas': contagem_saidas,
        'inicio_periodo': inicio_periodo.date(),
        'fim_periodo': fim_periodo.date(),
        'total_arrecadado': float(total_arrecadado),
        'total_custos': float(total_custos),
        'top_produtos': list(top_produtos),
        'top_categorias': list(top_categorias),
    }

    return render(request, 'periodo.html', contexto)


def consulta_categoria(request):
    """View para filtrar as movimentações de uma dada categoria nos ultimos 30 dias"""

    categorias = Categoria.objects.order_by('nome')
    categoria_selecionada = None
    movimentacoes = Movimentacao.objects.none()

    id_categoria = request.GET.get('categoria')
    
    if id_categoria:
        try:
            categoria_selecionada = Categoria.objects.get(pk=int(id_categoria))
            movimentacoes = Movimentacao.objects.filter(produto__categoria=categoria_selecionada)
        except (Categoria.DoesNotExist, ValueError):
            categoria_selecionada = None
            movimentacoes = Movimentacao.objects.none()

    trinta_dias_atras = timezone.now() - timedelta(days=30)
    movimentacoes_30dias = movimentacoes.filter(data__gte=trinta_dias_atras)

    contagem_entradas = movimentacoes_30dias.filter(tipo='entrada').count()
    contagem_saidas = movimentacoes_30dias.filter(tipo='saida').count()

    movimentacoes_pagina = paginar(request, movimentacoes_30dias.order_by('data'))
    query_string = montar_query_string(request)


    total_arrecadado = total_por_tipo(movimentacoes_30dias, 'saida')
    total_custos = total_por_tipo(movimentacoes_30dias, 'entrada')

    produtos_mais_vendidos = []
    produtos_menos_vendidos = []

    if categoria_selecionada:
        produtos_vendidos_quantidade = movimentacoes_30dias.filter(tipo='saida').values('produto_nome').annotate(
            total_quantidade=Sum('quantidade')
        )
        produtos_mais_vendidos = list(produtos_vendidos_quantidade.order_by('-total_quantidade')[:3])
        produtos_menos_vendidos = list(produtos_vendidos_quantidade.order_by('total_quantidade')[:3])

    contexto = {
        'categorias': categorias,
        'categoria_selecionada': categoria_selecionada,
        'movimentacoes_categoria': movimentacoes_pagina,
        'page_obj': movimentacoes_pagina,
        'query_string': query_string,
        'contagem_entradas': contagem_entradas,
        'contagem_saidas': contagem_saidas,
        'total_arrecadado': float(total_arrecadado),
        'total_custos': float(total_custos),
        'produtos_mais_vendidos': produtos_mais_vendidos,
        'produtos_menos_vendidos': produtos_menos_vendidos,
        'periodo_label': 'Últimos 30 dias',
    }

    return render(request, 'consulta_categoria.html', contexto)


def consulta_produto(request):
    """View para exibir o formulário de consulta por produto."""
    produtos = Produto.objects.order_by('nome')
    produto_selecionado_id = request.GET.get('produto', '')
    produto_selecionado = None

    contexto = {
        'produtos': produtos,
        'produto_selecionado_id': produto_selecionado_id,
        'produto_selecionado': produto_selecionado,
    }

    if produto_selecionado_id:
        try:
            produto_selecionado = Produto.objects.get(pk=int(produto_selecionado_id))
        except (Produto.DoesNotExist, ValueError):
            produto_selecionado = None

    if not produto_selecionado:
        return render(request, 'consulta_produto.html', contexto)

    trinta_dias_atras = timezone.now() - timedelta(days=30)
    movimentacoes_30dias = Movimentacao.objects.filter(produto=produto_selecionado, data__gte=trinta_dias_atras)

    receita_30dias = total_por_tipo(movimentacoes_30dias, 'saida')
    entrada_quantidade_30dias = movimentacoes_30dias.filter(tipo='entrada').aggregate(total=Sum('quantidade'))['total']
    if entrada_quantidade_30dias is None:
        entrada_quantidade_30dias = 0

    saida_quantidade_30dias = movimentacoes_30dias.filter(tipo='saida').aggregate(total=Sum('quantidade'))['total']
    if saida_quantidade_30dias is None:
        saida_quantidade_30dias = 0

    unidades_perdidas_30dias = movimentacoes_30dias.filter(
        tipo='saida'
    ).filter(
        Q(custo_unitario__isnull=True) | Q(custo_unitario=0)
    ).aggregate(total=Sum('quantidade'))['total']
    if unidades_perdidas_30dias is None:
        unidades_perdidas_30dias = 0

    estoque_atual = produto_selecionado.quantidade
    estoque_inicial_30dias = max(0, estoque_atual - entrada_quantidade_30dias + saida_quantidade_30dias)
    estoque_medio_30dias = (estoque_inicial_30dias + estoque_atual) / 2 if estoque_atual or estoque_inicial_30dias else 0
    giro_30dias = (receita_30dias / estoque_medio_30dias) if estoque_medio_30dias else 0

    contexto.update({
        'produto_selecionado': produto_selecionado,
        'estoque_atual': estoque_atual,
        'valor_unitario': produto_selecionado.preco,
        'receita_estoque_atual': produto_selecionado.preco * estoque_atual,
        'receita_30dias': receita_30dias,
        'unidades_perdidas_30dias': unidades_perdidas_30dias,
        'giro_30dias': giro_30dias,
    })

    return render(request, 'consulta_produto.html', contexto)


def page_not_found(request, exception):
    return render(request, '404.html', status=404)


def server_error(request):
    return render(request, '500.html', status=500)


def permission_denied(request, exception):
    return render(request, '401.html', status=401)
