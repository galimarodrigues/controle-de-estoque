from datetime import datetime, timedelta

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import F, FloatField, Max, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone

from estoque.models import Movimentacao
from .forms import PeriodoConsultaForm


def periodo(request):
    form = PeriodoConsultaForm(request.GET or None)
    # Por padrao, o calendario selecionará o periodo correspondente aos sete dias
    data_inicio = timezone.now() - timedelta(days=7)
    data_fim = timezone.now()

    if form.is_valid():
        data_inicio = timezone.make_aware(datetime.combine(form.cleaned_data['data_inicio'], datetime.min.time()))
        data_fim = timezone.make_aware(datetime.combine(form.cleaned_data['data_fim'], datetime.max.time()))

    movimentacoes = Movimentacao.objects.filter(
        data__gte=data_inicio,
        data__lte=data_fim,
    )

    entrada_count = movimentacoes.filter(tipo='entrada').count()
    saida_count = movimentacoes.filter(tipo='saida').count()

    movimentacoes_ordenadas = movimentacoes.order_by('data')
    paginator = Paginator(movimentacoes_ordenadas, 50)
    page_number = request.GET.get('page', 1)

    try:
        movimentacoes_pagina = paginator.page(page_number)
    except PageNotAnInteger:
        movimentacoes_pagina = paginator.page(1)
    except EmptyPage:
        movimentacoes_pagina = paginator.page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    query_string = query_params.urlencode()
    if query_string:
        query_string = '&' + query_string

    valor_por_movimentacao = F('quantidade') * Coalesce(
        'custo_unitario',
        F('produto__preco'),
        output_field=FloatField(),
    )

    # Calcular total arrecadado apenas das saídas
    total_arrecadado = movimentacoes.filter(tipo='saida').aggregate(
        total=Coalesce(Sum(valor_por_movimentacao), 0, output_field=FloatField())
    )['total'] or 0

    # Calcular total de custos das entradas
    total_custos = movimentacoes.filter(tipo='entrada').aggregate(
        total=Coalesce(Sum(valor_por_movimentacao), 0, output_field=FloatField())
    )['total'] or 0

    # Top 5 produtos mais vendidos por valor
    top_produtos = movimentacoes.filter(tipo='saida').values('produto__nome').annotate(
        total_vendas=Coalesce(Sum(valor_por_movimentacao), 0, output_field=FloatField())
    ).order_by('-total_vendas')[:5]

    # Top 5 categorias mais vendidas por valor
    top_categorias = movimentacoes.filter(tipo='saida').values('produto__categoria__nome').annotate(
        total_vendas=Coalesce(Sum(valor_por_movimentacao), 0, output_field=FloatField())
    ).order_by('-total_vendas')[:5]

    return render(request, 'periodo.html', {
        'form': form,
        'movimentacoes_periodo': movimentacoes_pagina,
        'page_obj': movimentacoes_pagina,
        'query_string': query_string,
        'entrada_count': entrada_count,
        'saida_count': saida_count,
        'inicio_periodo': data_inicio.date(),
        'fim_periodo': data_fim.date(),
        'total_arrecadado': float(total_arrecadado),
        'total_custos': float(total_custos),
        'top_produtos': list(top_produtos),
        'top_categorias': list(top_categorias),
    })


def page_not_found(request, exception):
    return render(request, '404.html', status=404)


def server_error(request):
    return render(request, '500.html', status=500)


def permission_denied(request, exception):
    return render(request, '401.html', status=401)
