#!/usr/bin/env python
import argparse
import html
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from http.cookiejar import CookieJar
from pathlib import Path


UNIDADE_MAP = {
    "kg": "kg",
    "litros": "l",
    "unidades": "un",
    "caixas": "cx",
    "pacotes": "pct",
    "fardos": "cx",
    "macos": "un",
}


FORNECEDORES = [
    "Fornecedor Central",
    "Distribuidora Vale",
    "Atacado Mantiqueira",
    "Cooperativa Cafeeira",
    "Casa de Embalagens",
]


MOTIVOS_ENTRADA = [
    "Reposicao semanal",
    "Compra programada",
    "Recebimento de fornecedor",
]


MOTIVOS_SAIDA = [
    "Consumo operacional",
    "Producao diaria",
    "Ajuste de estoque",
    "Venda registrada",
    "Perda operacional",
]


LOW_STOCK_PRODUCTS = {
    "Cha Matcha",
    "Chocolate em Barra para Raspas",
    "Touca Descartavel",
    "Sacola Kraft",
    "Gengibre",
}


SEED_MARKER = "[seed_prod:doug-braz-history]"


BASE_DATA = {
    "Graos e Cafes": [
        ("Cafe Especial Mogiana", "kg", "78.50", 42),
        ("Cafe Bourbon Amarelo", "kg", "84.90", 35),
        ("Cafe Catuai Vermelho", "kg", "72.40", 28),
        ("Cafe Descafeinado", "kg", "69.90", 18),
        ("Graos para Espresso", "kg", "81.75", 40),
        ("Cafe Organico Mantiqueira", "kg", "88.30", 24),
        ("Blend Casa Intenso", "kg", "76.20", 31),
        ("Blend Casa Suave", "kg", "73.80", 29),
    ],
    "Leites e Derivados": [
        ("Leite Integral", "litros", "6.90", 90),
        ("Leite Desnatado", "litros", "7.10", 55),
        ("Leite Sem Lactose", "litros", "8.40", 48),
        ("Bebida de Aveia", "litros", "13.90", 26),
        ("Bebida de Amendoas", "litros", "15.50", 22),
        ("Creme de Leite Fresco", "litros", "18.75", 18),
        ("Manteiga sem Sal", "unidades", "9.20", 36),
        ("Queijo Cream Cheese", "unidades", "11.80", 30),
    ],
    "Xaropes e Coberturas": [
        ("Xarope de Baunilha", "unidades", "24.90", 20),
        ("Xarope de Caramelo", "unidades", "25.40", 18),
        ("Xarope de Avela", "unidades", "28.10", 16),
        ("Calda de Chocolate", "unidades", "19.90", 25),
        ("Calda de Morango", "unidades", "18.60", 19),
        ("Mel Silvestre", "unidades", "21.75", 14),
        ("Canela em Po Premium", "unidades", "13.20", 27),
        ("Chocolate em Po 50%", "kg", "32.40", 21),
    ],
    "Chas e Infusoes": [
        ("Cha Verde", "caixas", "14.90", 26),
        ("Cha de Hibisco", "caixas", "13.50", 22),
        ("Cha de Camomila", "caixas", "12.80", 24),
        ("Cha Preto Ingles", "caixas", "15.40", 18),
        ("Cha de Frutas Vermelhas", "caixas", "16.10", 17),
        ("Infusao de Capim Cidreira", "caixas", "11.90", 20),
        ("Cha de Hortela", "caixas", "12.60", 19),
        ("Infusao Digestiva", "caixas", "13.10", 15),
    ],
    "Sucos e Polpas": [
        ("Polpa de Laranja", "kg", "17.90", 32),
        ("Polpa de Maracuja", "kg", "21.40", 24),
        ("Polpa de Acerola", "kg", "19.70", 20),
        ("Polpa de Manga", "kg", "18.30", 22),
        ("Suco de Uva Integral", "litros", "16.50", 28),
        ("Suco de Maca Integral", "litros", "15.90", 25),
        ("Agua de Coco", "litros", "11.40", 34),
        ("Pure de Morango", "kg", "27.80", 14),
    ],
    "Panificacao": [
        ("Pao de Queijo Congelado", "kg", "26.90", 30),
        ("Croissant Tradicional", "unidades", "5.80", 80),
        ("Massa para Waffle", "kg", "18.40", 22),
        ("Pao Brioche", "unidades", "4.90", 54),
        ("Mini Baguete", "unidades", "3.40", 60),
        ("Cookie Artesanal", "unidades", "4.60", 72),
        ("Brownie de Chocolate", "unidades", "6.20", 44),
        ("Muffin de Banana", "unidades", "5.70", 38),
    ],
    "Doces e Confeitaria": [
        ("Acucar Refinado", "kg", "5.40", 50),
        ("Acucar Mascavo", "kg", "8.70", 22),
        ("Leite Condensado", "unidades", "7.90", 34),
        ("Doce de Leite Cremoso", "unidades", "12.80", 20),
        ("Granulado de Chocolate", "unidades", "9.60", 17),
        ("Gotas de Chocolate", "kg", "29.90", 15),
        ("Confeito Colorido", "unidades", "8.20", 14),
        ("Marshmallow Mini", "unidades", "10.50", 16),
    ],
    "Embalagens": [
        ("Copo 200ml", "pacotes", "18.90", 40),
        ("Copo 300ml", "pacotes", "22.50", 36),
        ("Tampa para Copo 200ml", "pacotes", "11.40", 30),
        ("Tampa para Copo 300ml", "pacotes", "12.70", 28),
        ("Canudo Biodegradavel", "pacotes", "9.80", 26),
        ("Sacola Kraft", "pacotes", "17.30", 18),
        ("Guardanapo Folha Dupla", "fardos", "24.60", 14),
        ("Porta Copo", "pacotes", "16.20", 20),
    ],
    "Descartaveis e Limpeza": [
        ("Detergente Neutro", "unidades", "4.90", 24),
        ("Desinfetante", "unidades", "8.30", 18),
        ("Pano Multiuso", "pacotes", "9.50", 15),
        ("Luva Descartavel", "caixas", "21.90", 12),
        ("Touca Descartavel", "pacotes", "13.40", 10),
        ("Papel Toalha", "fardos", "19.80", 14),
        ("Saco de Lixo 50L", "pacotes", "16.70", 11),
        ("Alcool 70%", "unidades", "10.60", 16),
    ],
    "Frutas e Frescos": [
        ("Banana Prata", "kg", "7.90", 18),
        ("Morango Fresco", "kg", "24.50", 16),
        ("Limao Tahiti", "kg", "6.80", 20),
        ("Maracuja Fresco", "kg", "11.90", 14),
        ("Maca Gala", "kg", "8.70", 22),
        ("Abacaxi Perola", "unidades", "9.60", 10),
        ("Hortela Fresca", "macos", "4.20", 15),
        ("Gengibre", "kg", "14.30", 12),
    ],
    "Salgados e Recheios": [
        ("Frango Desfiado", "kg", "29.40", 20),
        ("Recheio de Presunto e Queijo", "kg", "31.90", 18),
        ("Carne Seca Desfiada", "kg", "52.80", 12),
        ("Palmito Picado", "kg", "26.50", 14),
        ("Molho de Tomate Artesanal", "kg", "13.60", 20),
        ("Catupiry Culinario", "kg", "24.90", 16),
        ("Milho Verde", "unidades", "4.10", 30),
        ("Ervilha", "unidades", "4.00", 26),
    ],
    "Complementos de Barista": [
        ("Filtro de Papel V60", "caixas", "18.20", 12),
        ("Filtro de Papel 103", "caixas", "9.70", 25),
        ("Mexedor de Madeira", "pacotes", "7.40", 22),
        ("Chocolate em Barra para Raspas", "kg", "41.60", 10),
        ("Cacau Alcalino", "kg", "36.80", 11),
        ("Cha Matcha", "unidades", "39.90", 8),
        ("Canela em Pau", "pacotes", "12.50", 13),
        ("Raspas de Laranja Desidratada", "unidades", "15.30", 9),
    ],
}


@dataclass(frozen=True)
class ProdutoSeed:
    nome: str
    categoria: str
    unidade: str
    preco: str
    quantidade_inicial: int
    quantidade_final: int


@dataclass(frozen=True)
class MovimentacaoSeed:
    produto: str
    tipo: str
    quantidade: int
    custo_unitario: str
    motivo: str
    fornecedor: str
    observacao: str
    dias_atras: int = 0


class SeedClient:
    def __init__(self, base_url: str, pause_seconds: float = 0.08):
        self.base_url = base_url.rstrip("/")
        self.pause_seconds = pause_seconds
        self.cookie_jar = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        self.opener.addheaders = [("User-Agent", "estoque-seed-script/1.0")]

    def fetch_tables_page(self) -> str:
        last_error = None
        for attempt in range(1, 5):
            try:
                with self.opener.open(
                    f"{self.base_url}/estoque/tabelas/",
                    timeout=45,
                ) as response:
                    return response.read().decode("utf-8")
            except urllib.error.URLError as exc:
                last_error = exc
                if attempt == 4:
                    break
                time.sleep(attempt * 2)
        raise last_error

    def post_form(self, path: str, data: dict[str, str]) -> None:
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=encoded,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/estoque/tabelas/",
            },
        )
        last_error = None
        for attempt in range(1, 5):
            try:
                with self.opener.open(request, timeout=45) as response:
                    response.read()
                break
            except urllib.error.URLError as exc:
                last_error = exc
                if attempt == 4:
                    raise
                time.sleep(attempt * 2)
        if self.pause_seconds:
            time.sleep(self.pause_seconds)


def normalize_label(value: str) -> str:
    return " ".join(html.unescape(value).strip().split()).title()


def parse_csrf_token(page: str) -> str:
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page)
    if not match:
        raise RuntimeError("Nao foi possivel localizar o token CSRF na pagina de tabelas.")
    return match.group(1)


def parse_category_options(page: str) -> dict[str, str]:
    match = re.search(
        r'<select[^>]*id="produto-categoria"[^>]*>(.*?)</select>',
        page,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError("Nao foi possivel localizar a lista de categorias.")
    options = re.findall(r'<option value="(\d+)">(.*?)</option>', match.group(1), re.DOTALL)
    return {normalize_label(name): category_id for category_id, name in options}


def parse_existing_products(page: str) -> set[str]:
    tbody_match = re.search(r"<tbody>(.*?)</tbody>", page, re.DOTALL)
    if not tbody_match:
        return set()
    rows = re.findall(r"<tr>(.*?)</tr>", tbody_match.group(1), re.DOTALL)
    products = set()
    for row in rows:
        cells = re.findall(r"<td>(.*?)</td>", row, re.DOTALL)
        if cells:
            cell_text = re.sub(r"<.*?>", "", cells[0])
            normalized = " ".join(html.unescape(cell_text).strip().split())
            if normalized:
                products.add(normalized)
    return products


def parse_product_options(page: str, select_id: str) -> dict[str, str]:
    match = re.search(
        rf'<select[^>]*id="{re.escape(select_id)}"[^>]*>(.*?)</select>',
        page,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"Nao foi possivel localizar a lista de produtos do campo {select_id}.")
    options = re.findall(r'<option value="(\d+)">(.*?)</option>', match.group(1), re.DOTALL)
    return {" ".join(html.unescape(name).strip().split()): product_id for product_id, name in options}


def parse_existing_movement_counts(page: str) -> dict[str, int]:
    match = re.search(
        r'<table[^>]*id="datatablesMovimentacoes"[^>]*>(.*?)</table>',
        page,
        re.DOTALL,
    )
    if not match:
        return {}

    rows = re.findall(r"<tr>(.*?)</tr>", match.group(1), re.DOTALL)
    counts: dict[str, int] = {}
    for row in rows:
        cells = re.findall(r"<td>(.*?)</td>", row, re.DOTALL)
        if len(cells) < 2:
            continue
        product_name = re.sub(r"<.*?>", "", cells[1])
        normalized = " ".join(html.unescape(product_name).strip().split())
        if normalized and normalized != "Nenhuma movimentacao registrada ainda.":
            counts[normalized] = counts.get(normalized, 0) + 1
    return counts


def build_seed_products(seed: int) -> list[ProdutoSeed]:
    randomizer = random.Random(seed)
    products: list[ProdutoSeed] = []
    for category_name, entries in BASE_DATA.items():
        for nome, unidade, preco, quantidade in entries:
            unidade_padronizada = UNIDADE_MAP[unidade]
            price = Decimal(preco)
            adjusted_price = (price * Decimal(str(randomizer.uniform(0.93, 1.12)))).quantize(
                Decimal("0.01")
            )
            if nome in LOW_STOCK_PRODUCTS:
                adjusted_quantity = randomizer.randint(2, 5)
                quantidade_inicial = adjusted_quantity + randomizer.randint(48, 72)
            else:
                adjusted_quantity = max(quantidade + randomizer.randint(-5, 18), 4)
                quantidade_inicial = adjusted_quantity + randomizer.randint(18, 42)
            products.append(
                ProdutoSeed(
                    nome=nome,
                    categoria=category_name,
                    unidade=unidade_padronizada,
                    preco=str(adjusted_price),
                    quantidade_inicial=quantidade_inicial,
                    quantidade_final=adjusted_quantity,
                )
            )
    return products


def split_positive(total: int, parts: int, randomizer: random.Random) -> list[int]:
    if total <= 0:
        return []
    parts = max(1, min(parts, total))
    values = [1] * parts
    remaining = total - parts
    while remaining > 0:
        index = randomizer.randrange(parts)
        incremento = randomizer.randint(1, min(4, remaining))
        values[index] += incremento
        remaining -= incremento
    randomizer.shuffle(values)
    return values


def build_saida_days(count: int, randomizer: random.Random) -> list[int]:
    base_days = [0, 1, 2, 3, 5, 7, 10, 14, 21, 28, 35, 49, 63, 84, 112, 145, 178]
    days = []
    for index in range(count):
        base_day = base_days[index % len(base_days)]
        days.append(min(180, base_day + randomizer.randint(0, 3)))
    return days


def build_seed_movements(products: list[ProdutoSeed], seed: int) -> dict[str, list[MovimentacaoSeed]]:
    randomizer = random.Random(seed + 101)
    movimentacoes_por_produto: dict[str, list[MovimentacaoSeed]] = {}

    for item in products:
        saldo = item.quantidade_inicial
        movimentos: list[MovimentacaoSeed] = []

        entradas_extra = [
            (randomizer.randint(3, 9), randomizer.choice([24, 38, 57, 76, 96, 125])),
            (randomizer.randint(2, 8), randomizer.choice([9, 16, 31, 68, 104, 151])),
        ]
        for quantidade_entrada, dias_atras in entradas_extra:
            saldo += quantidade_entrada
            movimentos.append(
                MovimentacaoSeed(
                    produto=item.nome,
                    tipo="entrada",
                    quantidade=quantidade_entrada,
                    custo_unitario=item.preco,
                    motivo=randomizer.choice(MOTIVOS_ENTRADA),
                    fornecedor=randomizer.choice(FORNECEDORES),
                    observacao=f"Reposicao registrada pelo script de seed {SEED_MARKER}",
                    dias_atras=dias_atras,
                )
            )

        total_saida = max(0, saldo - item.quantidade_final)
        quantidade_saidas = min(total_saida, randomizer.randint(8, 14))
        saidas = split_positive(total_saida, quantidade_saidas, randomizer)
        dias_saidas = build_saida_days(len(saidas), randomizer)

        for indice, (saida, dias_atras) in enumerate(zip(saidas, dias_saidas)):
            saldo -= saida
            is_perda = indice == len(saidas) - 1 and item.nome in LOW_STOCK_PRODUCTS
            movimentos.append(
                MovimentacaoSeed(
                    produto=item.nome,
                    tipo="saida",
                    quantidade=saida,
                    custo_unitario="0.00" if is_perda else item.preco,
                    motivo="Perda operacional" if is_perda else randomizer.choice(MOTIVOS_SAIDA),
                    fornecedor=randomizer.choice(FORNECEDORES),
                    observacao=f"Venda historica gerada pelo script de seed {SEED_MARKER}",
                    dias_atras=dias_atras,
                )
            )

        movimentos.sort(key=lambda movimento: movimento.dias_atras, reverse=True)
        movimentacoes_por_produto[item.nome] = movimentos

    return movimentacoes_por_produto


def seed_database_http(base_url: str, dry_run: bool, seed: int) -> None:
    client = SeedClient(base_url)
    page = client.fetch_tables_page()
    csrf_token = parse_csrf_token(page)
    existing_categories = parse_category_options(page)
    existing_products = parse_existing_products(page)
    existing_movement_counts = parse_existing_movement_counts(page)

    desired_categories = list(BASE_DATA.keys())
    desired_products = build_seed_products(seed)
    desired_movements = build_seed_movements(desired_products, seed)

    categories_to_create = [
        name for name in desired_categories if normalize_label(name) not in existing_categories
    ]
    products_to_create = [item for item in desired_products if item.nome not in existing_products]
    products_to_seed_movements = [
        item
        for item in desired_products
        if item.nome in existing_products and existing_movement_counts.get(item.nome, 0) <= 1
    ]
    movement_products = products_to_create + products_to_seed_movements
    movements_to_create = sum(len(desired_movements[item.nome]) for item in movement_products)

    print(f"Base URL: {base_url}")
    print(f"Categorias existentes: {len(existing_categories)}")
    print(f"Produtos existentes: {len(existing_products)}")
    print(f"Categorias a criar: {len(categories_to_create)}")
    print(f"Produtos a criar: {len(products_to_create)}")
    print(f"Produtos existentes a completar historico: {len(products_to_seed_movements)}")
    print(f"Movimentacoes a criar: {movements_to_create}")
    print("Aviso: o modo HTTP usa os formularios da aplicacao e nao consegue retroagir datas.")
    print("Para alimentar historico semanal/mensal, execute com --mode orm no ambiente do Django.")

    if dry_run:
        print("Dry-run ativo. Nenhuma alteracao foi enviada.")
        return

    created_categories = 0
    for category_name in categories_to_create:
        client.post_form(
            "/estoque/add_categoria/",
            {
                "csrfmiddlewaretoken": csrf_token,
                "nome": category_name,
            },
        )
        created_categories += 1

    if created_categories:
        page = client.fetch_tables_page()
        csrf_token = parse_csrf_token(page)
        existing_categories = parse_category_options(page)

    created_products = 0
    for item in products_to_create:
        category_id = existing_categories.get(normalize_label(item.categoria))
        if not category_id:
            raise RuntimeError(f"Categoria ausente apos cadastro: {item.categoria}")
        client.post_form(
            "/estoque/add_produto/",
            {
                "csrfmiddlewaretoken": csrf_token,
                "nome": item.nome,
                "categoria": category_id,
                "preco": item.preco,
                "quantidade_inicial": str(item.quantidade_inicial),
                "unidade": item.unidade,
                "motivo": "Estoque inicial",
                "fornecedor": "Seed automatica",
                "observacao": "Cadastro inicial gerado pelo script de seed",
            },
        )
        created_products += 1

    final_page = client.fetch_tables_page()
    final_categories = parse_category_options(final_page)
    final_products = parse_existing_products(final_page)
    final_product_ids = parse_product_options(final_page, "produto-entrada")
    final_movement_counts = parse_existing_movement_counts(final_page)
    movement_products = [
        item
        for item in desired_products
        if item.nome in final_products and (
            item.nome in {product.nome for product in products_to_create}
            or final_movement_counts.get(item.nome, 0) <= 1
        )
    ]

    created_movements = 0
    for item in movement_products:
        product_id = final_product_ids.get(item.nome)
        if not product_id:
            raise RuntimeError(f"Produto ausente apos cadastro: {item.nome}")
        for movimento in desired_movements[item.nome]:
            path = "/estoque/entrada_produto/" if movimento.tipo == "entrada" else "/estoque/remover_produto/"
            client.post_form(
                path,
                {
                    "csrfmiddlewaretoken": csrf_token,
                    "produto": product_id,
                    "quantidade": str(movimento.quantidade),
                    "custo_unitario": movimento.custo_unitario,
                    "motivo": movimento.motivo,
                    "fornecedor": movimento.fornecedor,
                    "observacao": movimento.observacao,
                },
            )
            created_movements += 1

    final_page = client.fetch_tables_page()
    final_categories = parse_category_options(final_page)
    final_products = parse_existing_products(final_page)

    print(f"Categorias criadas: {created_categories}")
    print(f"Produtos criados: {created_products}")
    print(f"Movimentacoes criadas: {created_movements}")
    print(f"Categorias finais: {len(final_categories)}")
    print(f"Produtos finais: {len(final_products)}")


def setup_django():
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cafeteria.settings")

    import django

    django.setup()


def seed_datetime(days_ago: int, index: int):
    from django.utils import timezone

    base = timezone.now() - timedelta(days=days_ago)
    return base.replace(
        hour=8 + (index % 10),
        minute=(index * 7) % 60,
        second=0,
        microsecond=0,
    )


def create_historical_movement(produto, movimento: MovimentacaoSeed, usuario, index: int):
    from estoque.models import Movimentacao

    created = Movimentacao.objects.create(
        produto=produto,
        produto_nome=produto.nome,
        categoria_nome=produto.categoria.nome,
        unidade=produto.unidade,
        quantidade=movimento.quantidade,
        tipo=movimento.tipo,
        usuario=usuario,
        custo_unitario=Decimal(movimento.custo_unitario),
        motivo=movimento.motivo,
        fornecedor=movimento.fornecedor,
        observacao=movimento.observacao,
    )
    Movimentacao.objects.filter(pk=created.pk).update(
        data=seed_datetime(movimento.dias_atras, index)
    )
    return created


def update_historical_movement(record, produto, movimento: MovimentacaoSeed, usuario, index: int):
    from estoque.models import Movimentacao

    Movimentacao.objects.filter(pk=record.pk).update(
        produto=produto,
        produto_nome=produto.nome,
        categoria_nome=produto.categoria.nome,
        unidade=produto.unidade,
        quantidade=movimento.quantidade,
        tipo=movimento.tipo,
        usuario=usuario,
        custo_unitario=Decimal(movimento.custo_unitario),
        motivo=movimento.motivo,
        fornecedor=movimento.fornecedor,
        observacao=movimento.observacao,
        data=seed_datetime(movimento.dias_atras, index),
    )


def seed_database_orm(dry_run: bool, seed: int) -> None:
    setup_django()

    from django.contrib.auth.models import User
    from django.db import transaction
    from django.utils import timezone
    from estoque.models import Categoria, Movimentacao, Produto, normalizar_nome_categoria

    desired_categories = list(BASE_DATA.keys())
    desired_products = build_seed_products(seed)
    desired_movements = build_seed_movements(desired_products, seed)
    historical_cutoff = timezone.now() - timedelta(days=30)

    existing_categories = {}
    for category_name in desired_categories:
        categoria = Categoria.objects.filter(
            nome__iexact=normalizar_nome_categoria(category_name)
        ).first()
        if categoria:
            existing_categories[category_name] = categoria
    existing_products = {
        produto.nome: produto
        for produto in Produto.objects.select_related("categoria").filter(
            nome__in=[item.nome for item in desired_products]
        )
    }

    categories_to_create = [
        name for name in desired_categories if name not in existing_categories
    ]
    products_to_create = [
        item for item in desired_products if item.nome not in existing_products
    ]
    seed_stats = []
    for item in desired_products:
        seed_movements = Movimentacao.objects.filter(
            produto_nome=item.nome,
            observacao__contains=SEED_MARKER,
        )
        initial_movement_exists = Movimentacao.objects.filter(
            produto_nome=item.nome,
            tipo="entrada",
            motivo="Estoque inicial",
            fornecedor="Seed automatica",
        ).exists()
        historical_seed_movements = seed_movements.filter(data__lte=historical_cutoff)
        missing_movements = max(0, len(desired_movements[item.nome]) - seed_movements.count())
        seed_stats.append({
            "item": item,
            "existing_seed_movements": seed_movements.count(),
            "historical_seed_movements": historical_seed_movements.count(),
            "missing_initial_movement": 0 if initial_movement_exists else 1,
            "missing_movements": missing_movements,
        })

    products_to_adjust_dates = [
        stat["item"]
        for stat in seed_stats
        if stat["existing_seed_movements"] and stat["historical_seed_movements"] == 0
    ]
    products_to_complete_history = [
        stat["item"]
        for stat in seed_stats
        if stat["missing_movements"] > 0
    ]
    movements_to_create = sum(
        stat["missing_initial_movement"] + stat["missing_movements"]
        for stat in seed_stats
    )
    movements_to_update = sum(
        min(stat["existing_seed_movements"], len(desired_movements[stat["item"].nome]))
        for stat in seed_stats
        if stat["existing_seed_movements"]
    )

    print("Modo ORM: seed direto no banco configurado pelo Django.")
    print(f"Categorias existentes do seed: {len(existing_categories)}")
    print(f"Produtos existentes do seed: {len(existing_products)}")
    print(f"Categorias a criar: {len(categories_to_create)}")
    print(f"Produtos a criar: {len(products_to_create)}")
    print(f"Produtos a redistribuir datas: {len(products_to_adjust_dates)}")
    print(f"Produtos a completar historico: {len(products_to_complete_history)}")
    print(f"Movimentacoes existentes a atualizar: {movements_to_update}")
    print(f"Movimentacoes historicas a criar: {movements_to_create}")

    if dry_run:
        print("Dry-run ativo. Nenhuma alteracao foi enviada.")
        return

    with transaction.atomic():
        usuario, _ = User.objects.get_or_create(username="seed_prod")
        usuario.set_unusable_password()
        usuario.save(update_fields=["password"])

        categorias = {}
        for category_name in desired_categories:
            categoria = Categoria.objects.filter(
                nome__iexact=normalizar_nome_categoria(category_name)
            ).first()
            if categoria is None:
                categoria = Categoria.objects.create(nome=category_name)
            categorias[category_name] = categoria

        produtos = {}
        for item in desired_products:
            produto, created = Produto.objects.get_or_create(
                nome=item.nome,
                defaults={
                    "categoria": categorias[item.categoria],
                    "preco": Decimal(item.preco),
                    "quantidade": item.quantidade_final,
                    "unidade": item.unidade,
                },
            )
            if not created:
                produto.categoria = categorias[item.categoria]
                produto.preco = Decimal(item.preco)
                produto.unidade = item.unidade
                produto.quantidade = item.quantidade_final
                produto.save()
            produtos[item.nome] = produto

        created_movements = 0
        updated_movements = 0
        for item in desired_products:
            produto = produtos[item.nome]
            entrada_inicial = MovimentacaoSeed(
                produto=item.nome,
                tipo="entrada",
                quantidade=item.quantidade_inicial,
                custo_unitario=item.preco,
                motivo="Estoque inicial",
                fornecedor="Seed automatica",
                observacao=f"Cadastro inicial historico gerado pelo script de seed {SEED_MARKER}",
                dias_atras=210,
            )

            initial_movement = Movimentacao.objects.filter(
                produto_nome=item.nome,
                tipo="entrada",
                motivo="Estoque inicial",
                fornecedor="Seed automatica",
            ).order_by("id").first()
            if initial_movement:
                update_historical_movement(
                    initial_movement,
                    produto,
                    entrada_inicial,
                    usuario,
                    created_movements + updated_movements,
                )
                updated_movements += 1
            else:
                create_historical_movement(
                    produto,
                    entrada_inicial,
                    usuario,
                    created_movements + updated_movements,
                )
                created_movements += 1

            existing_seed_movements = list(Movimentacao.objects.filter(
                produto_nome=item.nome,
                observacao__contains=SEED_MARKER,
            ).exclude(
                motivo="Estoque inicial",
            ).order_by("id"))

            for index, movimento in enumerate(desired_movements[item.nome]):
                global_index = created_movements + updated_movements
                if index < len(existing_seed_movements):
                    update_historical_movement(
                        existing_seed_movements[index],
                        produto,
                        movimento,
                        usuario,
                        global_index,
                    )
                    updated_movements += 1
                else:
                    create_historical_movement(produto, movimento, usuario, global_index)
                    created_movements += 1

            produto.quantidade = item.quantidade_final
            produto.save(update_fields=["quantidade"])

    print(f"Categorias criadas: {len(categories_to_create)}")
    print(f"Produtos criados: {len(products_to_create)}")
    print(f"Movimentacoes historicas atualizadas: {updated_movements}")
    print(f"Movimentacoes historicas criadas: {created_movements}")
    print(f"Categorias finais: {Categoria.objects.count()}")
    print(f"Produtos finais: {Produto.objects.count()}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Popula a aplicacao de controle de estoque com dados realistas de cafeteria."
    )
    parser.add_argument(
        "--mode",
        choices=["orm", "http"],
        default="orm",
        help="Modo de execucao. Use orm para criar historico com datas reais; http para usar formularios.",
    )
    parser.add_argument(
        "--base-url",
        default="https://controle-de-estoque-univesp.up.railway.app",
        help="URL base da aplicacao, usada apenas no modo http.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260331,
        help="Seed deterministica para pequenas variacoes nos dados.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra o que seria criado sem enviar dados.",
    )
    args = parser.parse_args()

    try:
        if args.mode == "orm":
            seed_database_orm(args.dry_run, args.seed)
        else:
            seed_database_http(args.base_url, args.dry_run, args.seed)
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
