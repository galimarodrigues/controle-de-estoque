from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Movimentacao, Produto


class EstoqueFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='123456')
        self.client.force_login(self.user)
        self.categoria = Categoria.objects.create(nome='Bebidas')

    def test_cria_produto_com_movimentacao_inicial(self):
        response = self.client.post(reverse('add_produto'), {
            'nome': 'Cafe',
            'categoria': self.categoria.id,
            'preco': '12.50',
            'unidade': 'kg',
            'quantidade_inicial': 8,
            'motivo': 'Compra inicial',
            'fornecedor': 'Fornecedor A',
            'observacao': 'Primeiro lote',
        })

        self.assertRedirects(response, reverse('tables'))
        produto = Produto.objects.get(nome='Cafe')
        self.assertEqual(produto.quantidade, 8)

        movimentacao = Movimentacao.objects.get(produto=produto)
        self.assertEqual(movimentacao.tipo, 'entrada')
        self.assertEqual(movimentacao.quantidade, 8)
        self.assertEqual(movimentacao.custo_unitario, Decimal('12.50'))
        self.assertEqual(movimentacao.usuario, self.user)
        self.assertEqual(movimentacao.produto_nome, 'Cafe')
        self.assertEqual(movimentacao.categoria_nome, 'Bebidas')

    def test_registra_entrada_de_estoque(self):
        produto = Produto.objects.create(
            nome='Leite',
            categoria=self.categoria,
            preco='6.50',
            quantidade=3,
            unidade='l',
        )

        response = self.client.post(reverse('entrada_produto'), {
            'produto': produto.id,
            'quantidade': 5,
            'custo_unitario': '7.00',
            'motivo': 'Reposicao semanal',
            'fornecedor': 'Laticinios',
            'observacao': 'Entrega de segunda',
        })

        self.assertRedirects(response, reverse('tables'))
        produto.refresh_from_db()
        self.assertEqual(produto.quantidade, 8)
        self.assertTrue(Movimentacao.objects.filter(produto=produto, tipo='entrada', quantidade=5).exists())

    def test_impede_estoque_negativo(self):
        produto = Produto.objects.create(
            nome='Acucar',
            categoria=self.categoria,
            preco='4.30',
            quantidade=2,
            unidade='kg',
        )

        response = self.client.post(reverse('remover_produto'), {
            'produto': produto.id,
            'quantidade': 5,
            'motivo': 'Consumo',
        })

        self.assertRedirects(response, reverse('tables'))
        produto.refresh_from_db()
        self.assertEqual(produto.quantidade, 2)
        self.assertFalse(Movimentacao.objects.filter(produto=produto, tipo='saida').exists())

    def test_edicao_de_produto_nao_reescreve_historico(self):
        produto = Produto.objects.create(
            nome='Pao',
            categoria=self.categoria,
            preco='1.50',
            quantidade=4,
            unidade='un',
        )
        Movimentacao.objects.create(
            produto=produto,
            produto_nome='Pao',
            categoria_nome='Bebidas',
            unidade='un',
            quantidade=4,
            tipo='entrada',
            usuario=self.user,
            custo_unitario='1.50',
            motivo='Estoque inicial',
        )

        nova_categoria = Categoria.objects.create(nome='Padaria')
        response = self.client.post(reverse('editar_produto'), {
            'produto': produto.id,
            'nome': 'Pao Frances',
            'categoria': nova_categoria.id,
            'preco': '1.80',
            'unidade': 'un',
        })

        self.assertRedirects(response, reverse('tables'))
        produto.refresh_from_db()
        self.assertEqual(produto.nome, 'Pao Frances')
        movimentacao = Movimentacao.objects.get(produto=produto)
        self.assertEqual(movimentacao.produto_nome, 'Pao')
        self.assertEqual(movimentacao.categoria_nome, 'Bebidas')
