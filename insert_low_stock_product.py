import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cafeteria.settings')
django.setup()

from estoque.models import Categoria, Produto, Movimentacao
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

# Criar ou obter categoria
categoria, created = Categoria.objects.get_or_create(
    nome='Bebidas',
    defaults={}
)
if created:
    print(f"✓ Categoria '{categoria.nome}' criada")
else:
    print(f"✓ Categoria '{categoria.nome}' já existe")

# Criar produto com estoque baixo
produto = Produto.objects.create(
    nome='Suco Natural - Laranja (1L)',
    categoria=categoria,
    preco=Decimal('8.50'),
    quantidade=12,  # Estoque atual baixo
    unidade='un'
)
print(f"✓ Produto '{produto.nome}' criado com estoque atual: {produto.quantidade} unidades")

# Obter usuário admin (ou criar se não existir)
user = User.objects.first()
if not user:
    user = User.objects.create_user(username='admin', password='admin')
    print(f"✓ Usuário '{user.username}' criado")

# Criar movimentações de entrada para estabelecer estoque médio histórico
# Estoque médio: (50 + 50 + 40) / 3 = 46.67
# 30% disso: ~14 unidades
# Estoque atual: 12 unidades (< 14, então está em baixo estoque)

movimentacoes_data = [
    {'quantidade': 50, 'dias_atras': 90},
    {'quantidade': 50, 'dias_atras': 60},
    {'quantidade': 40, 'dias_atras': 30},
]

for i, mov_data in enumerate(movimentacoes_data, 1):
    data = timezone.now() - timedelta(days=mov_data['dias_atras'])
    mov = Movimentacao.objects.create(
        produto=produto,
        produto_nome=produto.nome,
        categoria_nome=categoria.nome,
        unidade='un',
        quantidade=mov_data['quantidade'],
        tipo='entrada',
        data=data,
        usuario=user,
        custo_unitario=Decimal('5.50'),
        fornecedor='Fornecedor XYZ'
    )
    print(f"✓ Movimentação {i}: {mov.quantidade} unidades em {data.strftime('%d/%m/%Y')}")

# Calcular e exibir informações
total_entradas = sum(mov['quantidade'] for mov in movimentacoes_data)
media_historica = total_entradas / len(movimentacoes_data)
limite_baixo = media_historica * 0.3

print(f"\n📊 Resumo:")
print(f"   Estoque médio histórico: {media_historica:.2f} unidades")
print(f"   Limite de baixo estoque (30%): {limite_baixo:.2f} unidades")
print(f"   Estoque atual: {produto.quantidade} unidades")
print(f"   Status: {'⚠️  BAIXO ESTOQUE' if produto.quantidade < limite_baixo else '✓ Estoque ok'}")
