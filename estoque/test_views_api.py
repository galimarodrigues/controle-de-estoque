import json
import subprocess
from unittest.mock import patch

import pytest
from django.urls import reverse

from .models import Movimentacao, Produto
from .seed_runner import HARDCODED_SEED_API_KEY


@pytest.mark.django_db
def test_dashboard_exibe_resumo_do_estoque(cliente_autenticado, produto):
    response = cliente_autenticado.get(reverse('index'))

    assert response.status_code == 200
    assert response.context['resumo_estoque']['total_produtos'] == 1
    assert response.context['resumo_estoque']['total_itens'] == 10


@pytest.mark.django_db
def test_exclusao_de_produto_com_saldo_e_bloqueada(cliente_autenticado, produto):
    response = cliente_autenticado.post(reverse('remover_produto'), {
        'produto': produto.id,
        'remover_tudo': 'on',
    }, follow=True)

    assert response.redirect_chain
    assert Produto.objects.filter(id=produto.id).exists()
    assert 'Nao e permitido excluir produto com estoque disponivel' in response.content.decode()


@pytest.mark.django_db
def test_exclusao_de_produto_zerado_preserva_snapshot_historico(cliente_autenticado, produto, usuario):
    produto.quantidade = 0
    produto.save()
    movimentacao = Movimentacao.objects.create(
        produto=produto,
        produto_nome=produto.nome,
        categoria_nome=produto.categoria.nome,
        unidade=produto.unidade,
        quantidade=10,
        tipo='entrada',
        usuario=usuario,
        custo_unitario=produto.preco,
    )

    response = cliente_autenticado.post(reverse('remover_produto'), {
        'produto': produto.id,
        'remover_tudo': 'on',
    })

    movimentacao.refresh_from_db()
    assert response.status_code == 302
    assert not Produto.objects.filter(id=produto.id).exists()
    assert movimentacao.produto is None
    assert movimentacao.produto_nome == 'Cafe'


def test_seed_api_rejeita_metodo_e_chave_invalidos(client):
    method_response = client.get(reverse('run_seed_api'))
    key_response = client.post(reverse('run_seed_api'), {'seed_name': 'seed_prod_v2'})

    assert method_response.status_code == 405
    assert key_response.status_code == 403


def test_seed_api_rejeita_json_invalido(client):
    response = client.post(
        reverse('run_seed_api'),
        data='{invalido',
        content_type='application/json',
        HTTP_X_API_KEY=HARDCODED_SEED_API_KEY,
    )

    assert response.status_code == 400
    assert 'JSON invalido' in response.json()['detail']


@patch('estoque.views.get_supported_seed_names', return_value=['seed_prod_v2'])
@patch('estoque.views.run_seed')
def test_seed_api_retorna_sucesso_sem_executar_seed_real(mock_run_seed, _mock_supported, client):
    mock_run_seed.return_value = subprocess.CompletedProcess(
        args=['seed'], returncode=0, stdout='ok', stderr=''
    )

    response = client.post(
        reverse('run_seed_api'),
        data=json.dumps({'seed_name': 'seed_prod_v2', 'mode': 'orm', 'dry_run': True}),
        content_type='application/json',
        HTTP_X_API_KEY=HARDCODED_SEED_API_KEY,
    )

    assert response.status_code == 200
    assert response.json()['ok'] is True
    mock_run_seed.assert_called_once_with(
        seed_name='seed_prod_v2', mode='orm', dry_run=True, force_sqlite=True
    )


@patch('estoque.views.get_supported_seed_names', return_value=['seed_prod_v2'])
@patch('estoque.views.run_seed', side_effect=subprocess.TimeoutExpired(cmd='seed', timeout=30))
def test_seed_api_retorna_timeout(mock_run_seed, _mock_supported, client):
    response = client.post(
        reverse('run_seed_api'),
        data=json.dumps({}),
        content_type='application/json',
        HTTP_X_API_KEY=HARDCODED_SEED_API_KEY,
    )

    assert response.status_code == 504
    mock_run_seed.assert_called_once()
