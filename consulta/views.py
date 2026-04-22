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
        Q(custo_unitario__isnull=True) | Q(custo_unitario=0) # Perdas = saídas com custo unitário igual a zero ou nulo
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


def historico_vendas(request):
    """View para exibir o histórico de vendas da cafeteria."""

    produtos = Produto.objects.order_by('nome')
    produto_selecionado_id = request.GET.get('produto', '')

    produto_selecionado = None
    filtro_produto = {}
    if produto_selecionado_id:
        try:
            produto_selecionado = Produto.objects.get(pk=int(produto_selecionado_id))
            filtro_produto = {'produto': produto_selecionado}
        except (Produto.DoesNotExist, ValueError):
            produto_selecionado = None
            filtro_produto = {}

    contexto = {
        'produtos': produtos,
        'produto_selecionado_id': produto_selecionado_id,
        'produto_selecionado': produto_selecionado,
    }

    # Gráfico 1: Vendas do dia de hoje vs últimos 7 dias
    hoje = timezone.now().date()
    vendas_7dias = []
    labels_7dias = []
    
    for dias_atras in range(7, -1, -1):  # De 7 dias atrás até hoje
        data_atual = hoje - timedelta(days=dias_atras)
        inicio_dia = timezone.make_aware(datetime.combine(data_atual, datetime.min.time()))
        fim_dia = timezone.make_aware(datetime.combine(data_atual, datetime.max.time()))
        
        vendas_dia = Movimentacao.objects.filter(
            data__range=(inicio_dia, fim_dia),
            tipo='saida',
            **filtro_produto
        ).aggregate(total=Coalesce(Sum(valor_por_movimentacao()), 0, output_field=FloatField()))['total']
        
        vendas_7dias.append(float(vendas_dia))
        labels_7dias.append(data_atual.strftime('%d/%m'))

    # Gráfico 2: Vendas da semana atual vs últimas 4 semanas
    # Semana começa no domingo e termina no sábado
    hoje_semana = hoje - timedelta(days=hoje.weekday() + 1)  # Domingo da semana atual
    vendas_semanas = []
    labels_semanas = []
    
    for semanas_atras in range(4, -1, -1):  # Últimas 4 semanas + semana atual
        inicio_semana = hoje_semana - timedelta(weeks=semanas_atras)
        fim_semana = inicio_semana + timedelta(days=6)
        
        vendas_semana = Movimentacao.objects.filter(
            data__date__range=(inicio_semana, fim_semana),
            tipo='saida',
            **filtro_produto
        ).aggregate(total=Coalesce(Sum(valor_por_movimentacao()), 0, output_field=FloatField()))['total']
        
        vendas_semanas.append(float(vendas_semana))
        if semanas_atras == 0:
            labels_semanas.append('Atual')
        else:
            labels_semanas.append(f'{semanas_atras} sem. atrás')

    # Gráfico 3: Vendas do mês atual vs últimos 6 meses
    mes_atual = hoje.replace(day=1)
    vendas_meses = []
    labels_meses = []
    
    for meses_atras in range(6, -1, -1):  # Últimos 6 meses + mês atual
        inicio_mes = mes_atual - timedelta(days=30 * meses_atras)
        if meses_atras == 0:
            fim_mes = hoje
        else:
            # Próximo mês menos 1 dia
            proximo_mes = mes_atual - timedelta(days=30 * (meses_atras - 1))
            fim_mes = proximo_mes - timedelta(days=1)
        
        vendas_mes = Movimentacao.objects.filter(
            data__date__range=(inicio_mes, fim_mes),
            tipo='saida',
            **filtro_produto
        ).aggregate(total=Coalesce(Sum(valor_por_movimentacao()), 0, output_field=FloatField()))['total']
        
        vendas_meses.append(float(vendas_mes))
        if meses_atras == 0:
            labels_meses.append('Atual')
        else:
            labels_meses.append(f'{meses_atras} mês(es) atrás')

    contexto.update({
        'vendas_7dias': vendas_7dias,
        'labels_7dias': labels_7dias,
        'vendas_semanas': vendas_semanas,
        'labels_semanas': labels_semanas,
        'vendas_meses': vendas_meses,
        'labels_meses': labels_meses,
    })

    return render(request, 'historico_vendas.html', contexto)


def page_not_found(request, exception):
    return render(request, '404.html', status=404)


def server_error(request):
    return render(request, '500.html', status=500)


def permission_denied(request, exception):
    return render(request, '401.html', status=401)
