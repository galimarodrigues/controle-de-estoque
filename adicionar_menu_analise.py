from pathlib import Path

# Executar na raiz do projeto Django, onde existe a pasta templates/.
TEMPLATES = [
    "base.html",
    "charts.html",
    "consulta_categoria.html",
    "consulta_produto.html",
    "historico_vendas.html",
    "periodo.html",
    "tables.html",
]

MARCADOR = 'href="/analise/"'
BLOCO_REFERENCIA = '''                            <a tabindex="0" class="nav-link" href="/estoque/graficos/">
                                <div class="sb-nav-link-icon"><i class="fas fa-chart-area"></i></div>
                                Indicadores de Desempenho
                            </a>'''

LINK_ANALISE = '''                            <a tabindex="0" class="nav-link" href="/analise/">
                                <div class="sb-nav-link-icon"><i class="fas fa-brain"></i></div>
                                Análise de Dados
                            </a>'''

for nome in TEMPLATES:
    caminho = Path("templates") / nome

    if not caminho.exists():
        print(f"[IGNORADO] {caminho} não existe.")
        continue

    texto = caminho.read_text(encoding="utf-8")

    if MARCADOR in texto:
        print(f"[OK] {nome} já possui o link de Análise de Dados.")
        continue

    if BLOCO_REFERENCIA not in texto:
        print(f"[ERRO] Não encontrei o bloco esperado em {nome}. Nenhuma alteração feita.")
        continue

    novo_texto = texto.replace(
        BLOCO_REFERENCIA,
        BLOCO_REFERENCIA + "\n\n" + LINK_ANALISE,
        1,
    )

    caminho.write_text(novo_texto, encoding="utf-8")
    print(f"[ALTERADO] {nome}")

print("\nConcluído.")
