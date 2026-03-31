from decimal import Decimal

from django.db import transaction

from .models import Movimentacao, Produto


def registrar_movimentacao(
    *,
    produto_id,
    tipo,
    quantidade,
    usuario=None,
    custo_unitario=None,
    motivo='',
    fornecedor='',
    observacao='',
):
    produto = Produto.objects.select_for_update().select_related('categoria').get(pk=produto_id)

    if quantidade <= 0:
        raise ValueError('A quantidade deve ser maior que zero.')

    if tipo == 'saida' and quantidade > produto.quantidade:
        raise ValueError('Estoque insuficiente para registrar a saida.')

    if custo_unitario in (None, ''):
        custo_unitario = produto.preco

    if tipo == 'entrada':
        produto.quantidade += quantidade
    elif tipo == 'saida':
        produto.quantidade -= quantidade
    else:
        raise ValueError('Tipo de movimentacao invalido.')

    produto.save()

    movimentacao = Movimentacao.objects.create(
        produto=produto,
        produto_nome=produto.nome,
        categoria_nome=produto.categoria.nome,
        unidade=produto.unidade,
        quantidade=quantidade,
        tipo=tipo,
        usuario=usuario if getattr(usuario, 'is_authenticated', False) else None,
        custo_unitario=Decimal(custo_unitario),
        motivo=motivo.strip(),
        fornecedor=fornecedor.strip(),
        observacao=observacao.strip(),
    )
    return movimentacao


def criar_produto_com_estoque_inicial(
    *,
    nome,
    categoria,
    preco,
    unidade,
    quantidade_inicial,
    usuario=None,
    motivo='Estoque inicial',
    fornecedor='',
    observacao='',
):
    with transaction.atomic():
        produto = Produto.objects.create(
            nome=nome,
            categoria=categoria,
            preco=preco,
            quantidade=0,
            unidade=unidade,
        )

        if quantidade_inicial > 0:
            registrar_movimentacao(
                produto_id=produto.id,
                tipo='entrada',
                quantidade=quantidade_inicial,
                usuario=usuario,
                custo_unitario=preco,
                motivo=motivo,
                fornecedor=fornecedor,
                observacao=observacao,
            )

        return produto
