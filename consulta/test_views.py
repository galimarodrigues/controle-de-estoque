from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from estoque.models import Categoria, Movimentacao, Produto


def criar_movimentacao(*, produto, tipo, quantidade, data):
    movimentacao = Movimentacao.objects.create(
        produto=produto,
        produto_nome=produto.nome,
        categoria_nome=produto.categoria.nome,
        unidade=produto.unidade,
        quantidade=quantidade,
        tipo=tipo,
        custo_unitario=produto.preco,
    )
    Movimentacao.objects.filter(pk=movimentacao.pk).update(data=data)
    movimentacao.refresh_from_db()
    return movimentacao


@pytest.mark.django_db
def test_consulta_por_periodo_filtra_e_calcula_totais(cliente_autenticado, produto):
    agora = timezone.now()
    dentro_periodo = criar_movimentacao(produto=produto, tipo='saida', quantidade=2, data=agora)
    criar_movimentacao(produto=produto, tipo='entrada', quantidade=3, data=agora)
    criar_movimentacao(produto=produto, tipo='saida', quantidade=4, data=agora - timedelta(days=40))

    response = cliente_autenticado.get(reverse('consulta_periodo'), {
        'data_inicio': agora.date().isoformat(),
        'data_fim': agora.date().isoformat(),
    })

    assert response.status_code == 200
    assert response.context['contagem_entradas'] == 1
    assert response.context['contagem_saidas'] == 1
    assert response.context['total_arrecadado'] == 25.0
    assert dentro_periodo in response.context['page_obj'].object_list


@pytest.mark.django_db
def test_consulta_categoria_usa_apenas_movimentacoes_da_categoria(cliente_autenticado, produto):
    outra_categoria = Categoria.objects.create(nome='Padaria')
    outro_produto = Produto.objects.create(
        nome='Pao', categoria=outra_categoria, preco='1.50', quantidade=5, unidade='un'
    )
    criar_movimentacao(produto=produto, tipo='saida', quantidade=2, data=timezone.now())
    criar_movimentacao(produto=outro_produto, tipo='saida', quantidade=3, data=timezone.now())

    response = cliente_autenticado.get(reverse('consulta_categoria'), {'categoria': produto.categoria_id})

    assert response.status_code == 200
    assert response.context['categoria_selecionada'] == produto.categoria
    assert response.context['contagem_saidas'] == 1
    assert response.context['produtos_mais_vendidos'][0]['produto_nome'] == 'Cafe'


@pytest.mark.django_db
def test_consulta_produto_e_historico_exibem_indicadores(cliente_autenticado, produto):
    criar_movimentacao(produto=produto, tipo='entrada', quantidade=3, data=timezone.now())
    criar_movimentacao(produto=produto, tipo='saida', quantidade=2, data=timezone.now())

    produto_response = cliente_autenticado.get(reverse('consulta_produto'), {'produto': produto.id})
    historico_response = cliente_autenticado.get(reverse('historico_vendas'), {'produto': produto.id})

    assert produto_response.status_code == 200
    assert produto_response.context['estoque_atual'] == 10
    assert produto_response.context['receita_30dias'] == 25.0
    assert historico_response.status_code == 200
    assert len(historico_response.context['vendas_7dias']) == 8
    assert len(historico_response.context['vendas_semanas']) == 5
    assert len(historico_response.context['vendas_meses']) == 7
