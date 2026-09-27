import pytest
from django.contrib.auth.models import User

from estoque.models import Categoria, Produto


@pytest.fixture
def usuario(db):
    return User.objects.create_user(username='tester', password='senha-segura')


@pytest.fixture
def categoria(db):
    return Categoria.objects.create(nome='Bebidas')


@pytest.fixture
def produto(db, categoria):
    return Produto.objects.create(
        nome='Cafe', categoria=categoria, preco='12.50', quantidade=10, unidade='kg'
    )


@pytest.fixture
def cliente_autenticado(client, usuario):
    client.force_login(usuario)
    return client
