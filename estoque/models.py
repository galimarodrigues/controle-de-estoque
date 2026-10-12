from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


UNIDADES_VALIDAS = (
    ('un', 'Unidade'),
    ('cx', 'Caixa'),
    ('pct', 'Pacote'),
    ('g', 'Grama'),
    ('kg', 'Quilograma'),
    ('ml', 'Mililitro'),
    ('l', 'Litro'),
)


def normalizar_nome_categoria(nome):
    return ' '.join(nome.strip().split()).title()


def normalizar_unidade(unidade):
    return unidade.strip().lower()


class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['nome']

    def clean(self):
        self.nome = normalizar_nome_categoria(self.nome)
        existente = Categoria.objects.filter(nome__iexact=self.nome)
        if self.pk:
            existente = existente.exclude(pk=self.pk)
        if existente.exists():
            raise ValidationError({'nome': 'Ja existe uma categoria com este nome.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='produtos',
    )
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.PositiveIntegerField()
    unidade = models.CharField(max_length=20, choices=UNIDADES_VALIDAS)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['nome', 'categoria'],
                name='estoque_produto_unico_por_categoria',
            ),
        ]

    def clean_fields(self, exclude=None):
        if self.unidade:
            self.unidade = normalizar_unidade(self.unidade)
        super().clean_fields(exclude=exclude)

    def clean(self):
        self.unidade = normalizar_unidade(self.unidade)
        unidades_permitidas = {codigo for codigo, _ in UNIDADES_VALIDAS}
        if self.unidade not in unidades_permitidas:
            raise ValidationError({
                'unidade': 'Unidade invalida. Use uma das unidades padronizadas disponiveis.'
            })
        if self.preco < Decimal('0'):
            raise ValidationError({'preco': 'O preco nao pode ser negativo.'})
        if self.categoria_id and self.nome:
            nome_limpo = self.nome.strip()
            duplicado = Produto.objects.filter(
                nome__iexact=nome_limpo,
                categoria=self.categoria,
            )
            if self.pk:
                duplicado = duplicado.exclude(pk=self.pk)
            if duplicado.exists():
                raise ValidationError({
                    'nome': (
                        f'Ja existe um produto com este nome nesta categoria ("{nome_limpo}"). '
                        'Para repor ou aumentar a quantidade, utilize a opcao "Entrada Produto" para adicionar unidades ao mesmo item em vez de cadastra-lo novamente.'
                    )
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome


class Movimentacao(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saida'),
    ]

    produto = models.ForeignKey(
        Produto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes',
    )
    produto_nome = models.CharField(max_length=100, db_index=True)
    categoria_nome = models.CharField(max_length=100, db_index=True)
    unidade = models.CharField(max_length=20, choices=UNIDADES_VALIDAS)
    quantidade = models.PositiveIntegerField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, db_index=True)
    data = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    motivo = models.CharField(max_length=120, blank=True)
    fornecedor = models.CharField(max_length=120, blank=True)
    observacao = models.TextField(blank=True)

    class Meta:
        ordering = ['-data', '-id']
        indexes = [
            models.Index(fields=['data', 'tipo'], name='estoque_mov_data_tipo'),
            models.Index(fields=['produto', 'data'], name='estoque_mov_produto_data'),
            models.Index(fields=['categoria_nome', 'data'], name='estoque_mov_categ_data'),
        ]

    def clean_fields(self, exclude=None):
        if self.unidade:
            self.unidade = normalizar_unidade(self.unidade)
        super().clean_fields(exclude=exclude)

    def clean(self):
        self.unidade = normalizar_unidade(self.unidade)
        unidades_permitidas = {codigo for codigo, _ in UNIDADES_VALIDAS}
        if self.unidade not in unidades_permitidas:
            raise ValidationError({'unidade': 'A unidade da movimentacao eh invalida.'})

    def __str__(self):
        return f"{self.tipo} - {self.produto_nome} ({self.quantidade})"
