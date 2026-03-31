#!/usr/bin/env python
import argparse
import html
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from decimal import Decimal
from http.cookiejar import CookieJar


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
    quantidade: int


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
        with self.opener.open(f"{self.base_url}/estoque/tabelas/") as response:
            return response.read().decode("utf-8")

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
        with self.opener.open(request) as response:
            response.read()
        if self.pause_seconds:
            time.sleep(self.pause_seconds)


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
    return {html.unescape(name).strip(): category_id for category_id, name in options}


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
            normalized = html.unescape(cell_text).strip()
            if normalized:
                products.add(normalized)
    return products


def build_seed_products(seed: int) -> list[ProdutoSeed]:
    randomizer = random.Random(seed)
    products: list[ProdutoSeed] = []
    for category_name, entries in BASE_DATA.items():
        for nome, unidade, preco, quantidade in entries:
            price = Decimal(preco)
            adjusted_price = (price * Decimal(str(randomizer.uniform(0.93, 1.12)))).quantize(
                Decimal("0.01")
            )
            adjusted_quantity = max(quantidade + randomizer.randint(-5, 18), 4)
            products.append(
                ProdutoSeed(
                    nome=nome,
                    categoria=category_name,
                    unidade=unidade,
                    preco=str(adjusted_price),
                    quantidade=adjusted_quantity,
                )
            )
    return products


def seed_database(base_url: str, dry_run: bool, seed: int) -> None:
    client = SeedClient(base_url)
    page = client.fetch_tables_page()
    csrf_token = parse_csrf_token(page)
    existing_categories = parse_category_options(page)
    existing_products = parse_existing_products(page)

    desired_categories = list(BASE_DATA.keys())
    desired_products = build_seed_products(seed)

    categories_to_create = [name for name in desired_categories if name not in existing_categories]
    products_to_create = [item for item in desired_products if item.nome not in existing_products]

    print(f"Base URL: {base_url}")
    print(f"Categorias existentes: {len(existing_categories)}")
    print(f"Produtos existentes: {len(existing_products)}")
    print(f"Categorias a criar: {len(categories_to_create)}")
    print(f"Produtos a criar: {len(products_to_create)}")

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
        category_id = existing_categories.get(item.categoria)
        if not category_id:
            raise RuntimeError(f"Categoria ausente apos cadastro: {item.categoria}")
        client.post_form(
            "/estoque/add_produto/",
            {
                "csrfmiddlewaretoken": csrf_token,
                "nome": item.nome,
                "categoria": category_id,
                "preco": item.preco,
                "quantidade": str(item.quantidade),
                "unidade": item.unidade,
            },
        )
        created_products += 1

    final_page = client.fetch_tables_page()
    final_categories = parse_category_options(final_page)
    final_products = parse_existing_products(final_page)

    print(f"Categorias criadas: {created_categories}")
    print(f"Produtos criados: {created_products}")
    print(f"Categorias finais: {len(final_categories)}")
    print(f"Produtos finais: {len(final_products)}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Popula a aplicacao de controle de estoque via HTTP, usando os formularios reais da pagina."
    )
    parser.add_argument(
        "--base-url",
        default="https://controle-de-estoque-univesp.up.railway.app",
        help="URL base da aplicacao.",
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
        seed_database(args.base_url, args.dry_run, args.seed)
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
