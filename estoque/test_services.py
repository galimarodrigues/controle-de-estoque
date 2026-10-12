from decimal import Decimal

import pytest

from .models import Movimentacao
from .services import criar_produto_com_estoque_inicial, registrar_movimentacao


@pytest.mark.django_db
def test_registrar_entrada_atualiza_saldo_e_usa_preco_padrao(produto, usuario):
    movimentacao = registrar_movimentacao(
        produto_id=produto.id, tipo='entrada', quantidade=5, usuario=usuario, motivo='Reposicao'
    )

    produto.refresh_from_db()
    assert produto.quantidade == 15
    assert movimentacao.tipo == 'entrada'
    assert movimentacao.custo_unitario == Decimal('12.50')
    assert movimentacao.usuario == usuario
    assert movimentacao.produto_nome == 'Cafe'
    assert movimentacao.categoria_nome == 'Bebidas'


@pytest.mark.django_db
def test_registrar_saida_atualiza_saldo_e_registra_custo_informado(produto, usuario):
    movimentacao = registrar_movimentacao(
        produto_id=produto.id, tipo='saida', quantidade=3, usuario=usuario,
        custo_unitario='13.20', motivo='Venda'
    )

    produto.refresh_from_db()
    assert produto.quantidade == 7
    assert movimentacao.custo_unitario == Decimal('13.20')
    assert Movimentacao.objects.filter(produto=produto, tipo='saida').count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('tipo', 'quantidade', 'mensagem'),
    [
        ('entrada', 0, 'maior que zero'),
        ('invalido', 1, 'Tipo de movimentacao invalido'),
        ('saida', 11, 'Estoque insuficiente'),
    ],
)
def test_registrar_movimentacao_rejeita_dados_invalidos(produto, tipo, quantidade, mensagem):
    with pytest.raises(ValueError, match=mensagem):
        registrar_movimentacao(produto_id=produto.id, tipo=tipo, quantidade=quantidade)

    produto.refresh_from_db()
    assert produto.quantidade == 10
    assert Movimentacao.objects.count() == 0


@pytest.mark.django_db
def test_criar_produto_com_estoque_inicial_cria_historico(categoria, usuario):
    produto = criar_produto_com_estoque_inicial(
        nome='Leite', categoria=categoria, preco='6.50', unidade='l',
        quantidade_inicial=8, usuario=usuario, fornecedor='Laticinios'
    )

    produto.refresh_from_db()
    movimentacao = Movimentacao.objects.get(produto=produto)
    assert produto.quantidade == 8
    assert movimentacao.tipo == 'entrada'
    assert movimentacao.motivo == 'Estoque inicial'
    assert movimentacao.fornecedor == 'Laticinios'


@pytest.mark.django_db
def test_criar_produto_sem_estoque_inicial_nao_cria_movimentacao(categoria):
    produto = criar_produto_com_estoque_inicial(
        nome='Guardanapo', categoria=categoria, preco='2.00', unidade='pct', quantidade_inicial=0
    )

    assert produto.quantidade == 0
    assert not Movimentacao.objects.filter(produto=produto).exists()
