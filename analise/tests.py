from unittest.mock import patch

import pandas as pd
from django.test import TestCase


class DashboardAnaliseTests(TestCase):
    def test_sem_movimentacoes(self):
        response = self.client.get('/analise/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ainda não há movimentações de saída')

    @patch('analise.services.carregar_movimentacoes_dataframe')
    def test_sem_saidas(self, carregar):
        carregar.return_value = pd.DataFrame([{'tipo': 'entrada'}])
        response = self.client.get('/analise/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ainda não há movimentações de saída')

    @patch('analise.views.criar_dataset_produtos_kmeans')
    def test_poucos_produtos(self, criar):
        criar.return_value = pd.DataFrame([{'produto_nome': 'Café'}])
        response = self.client.get('/analise/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'pelo menos três produtos')
