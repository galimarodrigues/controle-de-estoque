#!/usr/bin/env python
import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from http.cookiejar import CookieJar
from pathlib import Path


SEED_MARKER = "[seed_prod_v2:json-history]"
SEED_DIR = Path(__file__).resolve().parent / "seed"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
UNIT_MAP = {
    "garrafa": "un",
    "lata": "un",
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
    data_original: str


class SeedClient:
    def __init__(self, base_url: str, pause_seconds: float = 0.08):
        self.base_url = base_url.rstrip("/")
        self.pause_seconds = pause_seconds
        self.cookie_jar = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        self.opener.addheaders = [("User-Agent", "estoque-seed-script/2.0")]

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


def normalize_unidade(unidade: str) -> str:
    unidade_normalizada = unidade.strip().lower()
    return UNIT_MAP.get(unidade_normalizada, unidade_normalizada)


def parse_seed_datetime(value: str) -> datetime:
    return datetime.strptime(value, DEFAULT_DATE_FORMAT)


def marker_observacao(observacao: str, data_original: str) -> str:
    texto = observacao.strip()
    sufixo = f"{SEED_MARKER} data={data_original}"
    if texto:
        return f"{texto} {sufixo}"
    return sufixo


def load_seed_data() -> tuple[list[str], list[ProdutoSeed], dict[str, list[MovimentacaoSeed]]]:
    categorias_path = SEED_DIR / "estoque_categoria.json"
    produtos_path = SEED_DIR / "estoque_produto.json"
    movimentacoes_path = SEED_DIR / "estoque_movimentacao.json"

    categorias_raw = json.loads(categorias_path.read_text(encoding="utf-8"))
    produtos_raw = json.loads(produtos_path.read_text(encoding="utf-8"))
    movimentacoes_raw = json.loads(movimentacoes_path.read_text(encoding="utf-8"))

    categorias_por_id = {item["id"]: item["nome"] for item in categorias_raw}
    movimentos_por_produto_id: dict[int, list[dict]] = defaultdict(list)
    for movimento in movimentacoes_raw:
        movimentos_por_produto_id[movimento["produto_id"]].append(movimento)

    categorias = [item["nome"] for item in categorias_raw]
    produtos: list[ProdutoSeed] = []
    movimentacoes_por_produto: dict[str, list[MovimentacaoSeed]] = {}

    for produto in produtos_raw:
        categoria_nome = categorias_por_id[produto["categoria_id"]]
        movimentos_raw = sorted(
            movimentos_por_produto_id.get(produto["id"], []),
            key=lambda item: parse_seed_datetime(item["data"]),
        )
        total_entradas = sum(
            int(item["quantidade"]) for item in movimentos_raw if item["tipo"] == "entrada"
        )
        total_saidas = sum(
            int(item["quantidade"]) for item in movimentos_raw if item["tipo"] == "saida"
        )
        quantidade_final = int(produto["quantidade"])
        quantidade_inicial = quantidade_final - total_entradas + total_saidas
        if quantidade_inicial < 0:
            raise RuntimeError(
                f"Quantidade inicial calculada invalida para {produto['nome']}: {quantidade_inicial}"
            )

        produto_seed = ProdutoSeed(
            nome=produto["nome"],
            categoria=categoria_nome,
            unidade=normalize_unidade(produto["unidade"]),
            preco=str(Decimal(str(produto["preco"])).quantize(Decimal("0.01"))),
            quantidade_inicial=quantidade_inicial,
            quantidade_final=quantidade_final,
        )
        produtos.append(produto_seed)
        movimentacoes_por_produto[produto_seed.nome] = [
            MovimentacaoSeed(
                produto=produto_seed.nome,
                tipo=item["tipo"],
                quantidade=int(item["quantidade"]),
                custo_unitario=str(
                    Decimal(str(item["custo_unitario"] or 0)).quantize(Decimal("0.01"))
                ),
                motivo=item.get("motivo", "") or "",
                fornecedor=item.get("fornecedor", "") or "",
                observacao=marker_observacao(item.get("observacao", "") or "", item["data"]),
                data_original=item["data"],
            )
            for item in movimentos_raw
        ]

    return categorias, produtos, movimentacoes_por_produto


def setup_django():
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cafeteria.settings")

    import django

    django.setup()


def seed_database_http(base_url: str, dry_run: bool) -> None:
    desired_categories, desired_products, desired_movements = load_seed_data()

    client = SeedClient(base_url)
    page = client.fetch_tables_page()
    csrf_token = parse_csrf_token(page)
    existing_categories = parse_category_options(page)
    existing_products = parse_existing_products(page)
    existing_movement_counts = parse_existing_movement_counts(page)

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
    print("Os dados sao lidos de scripts/seed/*.json e as unidades nao padronizadas viram 'un'.")

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
                "motivo": "Estoque inicial JSON",
                "fornecedor": "Seed automatica JSON",
                "observacao": f"Cadastro inicial gerado pelo script de seed {SEED_MARKER}",
            },
        )
        created_products += 1

    final_page = client.fetch_tables_page()
    final_product_ids = parse_product_options(final_page, "produto-entrada")
    final_products = parse_existing_products(final_page)
    final_movement_counts = parse_existing_movement_counts(final_page)
    created_names = {item.nome for item in products_to_create}
    movement_products = [
        item
        for item in desired_products
        if item.nome in final_products and (
            item.nome in created_names or final_movement_counts.get(item.nome, 0) <= 1
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


def create_historical_movement(produto, movimento: MovimentacaoSeed, usuario):
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
        data=parse_seed_datetime(movimento.data_original)
    )
    return created


def update_historical_movement(record, produto, movimento: MovimentacaoSeed, usuario):
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
        data=parse_seed_datetime(movimento.data_original),
    )


def seed_database_orm(dry_run: bool) -> None:
    setup_django()

    from django.contrib.auth.models import User
    from django.db import transaction
    from estoque.models import Categoria, Movimentacao, Produto, normalizar_nome_categoria

    desired_categories, desired_products, desired_movements = load_seed_data()

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
        seed_movements = list(
            Movimentacao.objects.filter(
                produto_nome=item.nome,
                observacao__contains=SEED_MARKER,
            ).order_by("data", "id")
        )
        desired_count = len(desired_movements[item.nome])
        seed_stats.append(
            {
                "item": item,
                "existing_seed_movements": len(seed_movements),
                "missing_movements": max(0, desired_count - len(seed_movements)),
            }
        )

    movements_to_create = sum(stat["missing_movements"] for stat in seed_stats)
    movements_to_update = sum(
        min(stat["existing_seed_movements"], len(desired_movements[stat["item"].nome]))
        for stat in seed_stats
    )

    print("Modo ORM: seed direto no banco configurado pelo Django.")
    print(f"Categorias existentes do seed: {len(existing_categories)}")
    print(f"Produtos existentes do seed: {len(existing_products)}")
    print(f"Categorias a criar: {len(categories_to_create)}")
    print(f"Produtos a criar: {len(products_to_create)}")
    print(f"Movimentacoes existentes a atualizar: {movements_to_update}")
    print(f"Movimentacoes historicas a criar: {movements_to_create}")
    print("Fonte de dados: scripts/seed/*.json")

    if dry_run:
        print("Dry-run ativo. Nenhuma alteracao foi enviada.")
        return

    with transaction.atomic():
        usuario, _ = User.objects.get_or_create(username="seed_prod_v2")
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
            existing_seed_movements = list(
                Movimentacao.objects.filter(
                    produto_nome=item.nome,
                    observacao__contains=SEED_MARKER,
                ).order_by("data", "id")
            )

            for index, movimento in enumerate(desired_movements[item.nome]):
                if index < len(existing_seed_movements):
                    update_historical_movement(
                        existing_seed_movements[index],
                        produto,
                        movimento,
                        usuario,
                    )
                    updated_movements += 1
                else:
                    create_historical_movement(produto, movimento, usuario)
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
        description="Popula a aplicacao de controle de estoque usando os JSONs da pasta scripts/seed."
    )
    parser.add_argument(
        "--mode",
        choices=["orm", "http"],
        default="orm",
        help="Modo de execucao. Use orm para preservar datas; http para usar formularios.",
    )
    parser.add_argument(
        "--base-url",
        default="https://controle-de-estoque-univesp.up.railway.app",
        help="URL base da aplicacao, usada apenas no modo http.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra o que seria criado sem enviar dados.",
    )
    args = parser.parse_args()

    try:
        if args.mode == "orm":
            seed_database_orm(args.dry_run)
        else:
            seed_database_http(args.base_url, args.dry_run)
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
