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
    nome = models.CharField(max_length=100)

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
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.PositiveIntegerField()
    unidade = models.CharField(max_length=20)

    def clean(self):
        self.unidade = normalizar_unidade(self.unidade)
        unidades_permitidas = {codigo for codigo, _ in UNIDADES_VALIDAS}
        if self.unidade not in unidades_permitidas:
            raise ValidationError({
                'unidade': 'Unidade invalida. Use uma das unidades padronizadas disponiveis.'
            })
        if self.preco < Decimal('0'):
            raise ValidationError({'preco': 'O preco nao pode ser negativo.'})

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

    produto = models.ForeignKey(Produto, on_delete=models.SET_NULL, null=True, blank=True)
    produto_nome = models.CharField(max_length=100)
    categoria_nome = models.CharField(max_length=100)
    unidade = models.CharField(max_length=20)
    quantidade = models.PositiveIntegerField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    data = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    motivo = models.CharField(max_length=120, blank=True)
    fornecedor = models.CharField(max_length=120, blank=True)
    observacao = models.TextField(blank=True)

    class Meta:
        ordering = ['-data', '-id']

    def clean(self):
        self.unidade = normalizar_unidade(self.unidade)
        unidades_permitidas = {codigo for codigo, _ in UNIDADES_VALIDAS}
        if self.unidade not in unidades_permitidas:
            raise ValidationError({'unidade': 'A unidade da movimentacao eh invalida.'})

    def __str__(self):
        return f"{self.tipo} - {self.produto_nome} ({self.quantidade})"
