# Melhorias PI 2026

## Tarefa 1: Estruturar a base de dados para analise

**Responsavel 1:** foco em backend e modelagem.

**Objetivo:** garantir que o sistema passe a registrar historico suficiente para analise real, nao apenas o estoque atual.

**Entregas:**

- Integrar de verdade o modelo `Movimentacao` ao sistema.
- Registrar toda entrada e saida de produto com data, quantidade, usuario e tipo.
- Criar fluxo para entradas de estoque, porque hoje o sistema so adiciona produto diretamente e remove quantidade.
- Ajustar edicao de produto para nao perder historico analitico.
- Criar dados derivados importantes, se necessario:
  - custo unitario no momento da movimentacao
  - motivo da movimentacao
  - fornecedor
  - observacao
- Garantir consistencia:
  - nao permitir estoque negativo
  - validar unidades
  - padronizar categorias

**Resultado esperado:**

- o projeto passa a ter serie historica
- fica possivel analisar consumo, reposicao, giro e sazonalidade

## Tarefa 2: Criar camada de indicadores e preparacao dos dados

**Responsavel 2:** foco em consultas, metricas e logica analitica.

**Objetivo:** transformar os dados brutos em metricas uteis para tomada de decisao.

**Entregas:**

- Criar consultas agregadas por periodo:
  - movimentacoes por dia, semana e mes
  - consumo por categoria
  - consumo por produto
  - valor total em estoque
  - produtos com maior saida
  - produtos parados
- Criar indicadores principais:
  - giro de estoque
  - ticket medio de reposicao
  - produtos com baixo estoque
  - categorias mais caras
  - perda potencial por excesso de estoque
- Criar uma camada de servico ou utilitarios analiticos no backend para centralizar esses calculos.
- Criar exportacao CSV ou JSON para analise externa.
- Se der tempo, adicionar previsao simples:
  - media movel de consumo
  - sugestao de reposicao por produto

**Resultado esperado:**

- o sistema passa a responder perguntas gerenciais, nao so listar produtos
- a analise deixa de ser visual apenas e vira metrica concreta

## Tarefa 3: Dashboard analitico e apresentacao dos insights

**Responsavel 3:** foco em frontend, UX e comunicacao dos resultados.

**Objetivo:** apresentar os dados de forma clara e util para o usuario final e para a entrega da faculdade.

**Entregas:**

- Reformular a pagina de graficos para exibir indicadores reais.
- Criar dashboard com cards e graficos como:
  - total de itens em estoque
  - valor estimado do estoque
  - produtos com menor quantidade
  - produtos com maior saida
  - categorias com maior consumo
  - evolucao temporal das movimentacoes
- Adicionar filtros:
  - por periodo
  - por categoria
  - por produto
- Criar tabelas analiticas:
  - ranking de produtos criticos
  - ranking de categorias
  - historico recente de movimentacoes
- Melhorar a apresentacao para a banca:
  - textos curtos de interpretacao dos graficos
  - destaque para problemas detectados
  - sugestoes automaticas de acao

**Resultado esperado:**

- o projeto ganha valor visual e gerencial
- fica mais facil demonstrar o impacto da analise de dados na apresentacao

## Sugestao de ordem

1. Tarefa 1 primeiro, porque sem historico a analise fica fraca.
2. Tarefa 2 em paralelo assim que a estrutura minima de movimentacao estiver pronta.
3. Tarefa 3 por ultimo, consumindo os indicadores criados.

## Escopo ideal para a faculdade

Se quiserem manter algo viavel para o semestre, eu faria como meta minima:

- registrar entradas e saidas corretamente
- criar metricas de consumo e baixo estoque
- montar um dashboard com filtros por periodo e categoria

