from datetime import datetime, timedelta

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import F, FloatField, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone

from estoque.models import Categoria, Movimentacao
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


def page_not_found(request, exception):
    return render(request, '404.html', status=404)


def server_error(request):
    return render(request, '500.html', status=500)


def permission_denied(request, exception):
    return render(request, '401.html', status=401)
