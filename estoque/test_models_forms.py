import pytest
from django.core.exceptions import ValidationError

from consulta.forms import PeriodoConsultaForm

from .forms import CategoriaForm, MovimentacaoForm, ProdutoForm
from .models import Categoria, Produto


@pytest.mark.django_db
def test_categoria_normaliza_nome():
    categoria = Categoria.objects.create(nome='  bebidas   quentes ')

    assert categoria.nome == 'Bebidas Quentes'


@pytest.mark.django_db
def test_categoria_rejeita_nome_duplicado_sem_diferenciar_maiusculas():
    Categoria.objects.create(nome='Bebidas')

    with pytest.raises(ValidationError, match='Ja existe uma categoria'):
        Categoria.objects.create(nome=' bebidas ')


@pytest.mark.django_db
def test_produto_normaliza_unidade():
    categoria = Categoria.objects.create(nome='Insumos')
    produto = Produto.objects.create(
        nome='Leite', categoria=categoria, preco='6.50', quantidade=1, unidade=' L '
    )

    assert produto.unidade == 'l'


@pytest.mark.django_db
def test_produto_rejeita_unidade_e_preco_invalidos(categoria):
    with pytest.raises(ValidationError, match='Unidade invalida'):
        Produto.objects.create(
            nome='Produto invalido', categoria=categoria, preco='1.00', quantidade=1, unidade='saco'
        )

    with pytest.raises(ValidationError, match='preco nao pode ser negativo'):
        Produto.objects.create(
            nome='Produto barato', categoria=categoria, preco='-1.00', quantidade=1, unidade='un'
        )


@pytest.mark.django_db
def test_formularios_validam_categoria_unidade_e_quantidade(categoria):
    categoria_form = CategoriaForm(data={'nome': ' bebidas '})
    produto_form = ProdutoForm(data={
        'nome': 'Acucar', 'categoria': categoria.id, 'preco': '4.30',
        'unidade': 'saco', 'quantidade_inicial': 0,
    })
    movimentacao_form = MovimentacaoForm(data={'produto': '', 'quantidade': 0})

    assert not categoria_form.is_valid()
    assert not produto_form.is_valid()
    assert not movimentacao_form.is_valid()


def test_formulario_periodo_rejeita_intervalo_invertido():
    form = PeriodoConsultaForm(data={'data_inicio': '2026-09-10', 'data_fim': '2026-09-01'})

    assert not form.is_valid()
    assert 'data de início deve ser anterior' in str(form.errors)
