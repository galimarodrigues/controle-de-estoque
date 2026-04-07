from datetime import datetime, timedelta

from django.db.models import F, FloatField, Max, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone

from estoque.models import Movimentacao
from .forms import PeriodoConsultaForm


def periodo(request):
    form = PeriodoConsultaForm(request.GET or None)
    data_inicio = timezone.now() - timedelta(days=7)
    data_fim = timezone.now()

    if form.is_valid():
        data_inicio = datetime.combine(form.cleaned_data['data_inicio'], datetime.min.time())
        data_fim = datetime.combine(form.cleaned_data['data_fim'], datetime.max.time())

    movimentacoes = Movimentacao.objects.filter(
        data__gte=data_inicio,
        data__lte=data_fim,
    )

    valor_por_movimentacao = F('quantidade') * Coalesce(
        'custo_unitario',
        F('produto__preco'),
        output_field=FloatField(),
    )

    # Calcular total arrecadado apenas das saídas
    total_arrecadado = movimentacoes.filter(tipo='saida').aggregate(
        total=Coalesce(Sum(valor_por_movimentacao), 0, output_field=FloatField())
    )['total'] or 0

    return render(request, 'consulta/periodo.html', {
        'form': form,
        'movimentacoes_periodo': movimentacoes.order_by('-data'),
        'inicio_periodo': data_inicio.date(),
        'fim_periodo': data_fim.date(),
        'total_arrecadado': float(total_arrecadado),
    })


def page_not_found(request, exception):
    return render(request, '404.html', status=404)


def server_error(request):
    return render(request, '500.html', status=500)


def permission_denied(request, exception):
    return render(request, '401.html', status=401)


