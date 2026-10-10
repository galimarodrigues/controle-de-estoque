# Controle de Estoque - Cafeteria
 
Aplicação web desenvolvida com Django para controle de estoque de uma cafeteria. O sistema permite gerenciar produtos, entradas e saídas de estoque, facilitando o acompanhamento e a organização dos insumos utilizados no estabelecimento.

Este projeto foi desenvolvido em equipe como parte do Projeto Integrador da UNIVESP, envolvendo alunos dos cursos de Engenharia de Computação, Bacharelado em Tecnologia da Informação e Ciência de Dados. O objetivo do projeto foi aplicar, na prática, conceitos de desenvolvimento de software, modelagem de dados e análise de informações, simulando um sistema real de gestão de estoque para pequenos negócios.

Além das funcionalidades de controle de estoque, o projeto passou a contar com um módulo de análise de dados e aprendizagem de máquina. Esse módulo prepara os históricos de movimentações, avalia uma tentativa de previsão de demanda e utiliza o algoritmo K-Means para agrupar produtos com comportamentos de consumo semelhantes.

A aplicação suporta execução local utilizando PostgreSQL e também pode ser implantada em produção através da plataforma Railway.
https://controle-de-estoque-univesp.up.railway.app/
 
## Tecnologias
- Python 3.10+
- Django
- PostgreSQL
- Pandas e NumPy (preparação e análise dos dados)
- scikit-learn (Random Forest, K-Means, PCA e métricas de avaliação)
- Bootstrap 5
- Chart.js (gráficos do módulo de análise)
- WhiteNoise (estáticos em produção)

## Requisitos
- Python 3.10+
- PostgreSQL 13+
- Git

Opcional (GUI): pgAdmin.

---

## Módulo de análise de dados e Machine Learning

O módulo de análise está disponível em `/analise/` e utiliza os registros de movimentação armazenados no banco configurado pelo Django. Seu objetivo é transformar o histórico operacional em informações que ajudem a compreender os padrões de consumo dos produtos.

O fluxo implementado é:

```text
PostgreSQL
    ↓
14.949 movimentações históricas
    ↓
Análise exploratória e preparação dos dados
    ↓
Experimento de previsão com Random Forest
    ↓
Avaliação e identificação de limitações
    ↓
K-Means para agrupamento dos produtos
    ↓
19 produtos agrupados em 2 clusters
    ↓
PCA para visualização em duas dimensões
    ↓
Django View
    ↓
Chart.js
    ↓
Dashboard de análise
```

### Preparação dos dados

- A base de demonstração analisada contém 14.949 movimentações: 13.733 saídas e 1.216 entradas.
- O conjunto contém 19 produtos e 5 categorias, com registros distribuídos por 151 dias.
- Para estudar a demanda, as saídas são agregadas por produto e dia.
- A preparação cria uma grade com todas as combinações de data e produto. Quando não há saída registrada em uma combinação, a demanda é preenchida com zero.
- Essa regra é uma premissa da análise: em uma base operacional real, a ausência de uma saída registrada precisa ser verificada antes de ser interpretada como ausência de demanda.
- A grade resultante contém 2.869 combinações de produto e dia. Depois da criação das variáveis históricas, 2.299 observações permanecem disponíveis para o experimento de previsão.

Os dados históricos incluídos no seed do projeto são de demonstração/simulados. Portanto, os resultados devem ser interpretados como resultados experimentais do conjunto utilizado, e não como evidência de desempenho em dados reais de uma cafeteria.

### Experimento de previsão com Random Forest

Foi testado o `RandomForestRegressor`, utilizando variáveis de calendário e de histórico, como dia da semana, demanda do dia anterior, demanda de sete dias antes e médias móveis de 7, 14 e 30 dias. A separação entre treinamento e teste respeita a ordem cronológica, evitando embaralhar indiscriminadamente observações do passado e do futuro.

Resultados obtidos no conjunto de teste:

| Modelo | MAE | RMSE | R² |
|---|---:|---:|---:|
| Média dos últimos 7 dias | 8,53 | 11,89 | -0,072 |
| Random Forest | 9,33 | 11,58 | -0,018 |
| Random Forest em duas etapas | 8,15 | 13,17 | -0,316 |

O primeiro Random Forest teve RMSE e R² ligeiramente melhores que a média de sete dias, mas MAE pior. A abordagem em duas etapas — primeiro classificar se haveria demanda e depois estimar a quantidade — reduziu o MAE, porém apresentou RMSE maior e R² mais baixo. No conjunto de teste, aproximadamente 66% das observações tinham demanda zero, e as correlações entre a demanda e as variáveis históricas testadas eram baixas.

Esses resultados indicaram que o histórico disponível não permitia uma previsão de demanda suficientemente consistente. Por isso, o projeto passou a enfatizar o agrupamento exploratório de produtos, em vez de apresentar a previsão como uma funcionalidade comprovadamente precisa.

### Agrupamento de produtos com K-Means

O K-Means é um algoritmo de aprendizagem não supervisionada. Diferentemente do Random Forest, ele não tenta prever uma quantidade futura: procura produtos com características históricas semelhantes.

Foi criado um conjunto com uma linha por produto e as seguintes características:

- demanda total;
- demanda média diária;
- desvio padrão da demanda;
- demanda máxima diária;
- número de dias com demanda;
- percentual de dias sem demanda;
- percentil 75 da demanda diária.

As variáveis foram padronizadas com `StandardScaler` antes do agrupamento. Foram comparados valores de K entre 2 e 6, utilizando o Silhouette Score. Entre os valores testados, `K = 2` apresentou a maior pontuação: aproximadamente `0,5672`.

A interpretação dos dois grupos encontrados foi:

| Grupo | Produtos | Características médias | Interpretação |
|---|---:|---|---|
| Cluster 0 | 8 | Demanda média de 9,44; cerca de 82 dias com demanda; aproximadamente 46% de dias sem demanda | Produtos com consumo mais frequente e demanda média mais elevada. |
| Cluster 1 | 11 | Demanda média de 4,46; cerca de 27 dias com demanda; aproximadamente 82% de dias sem demanda | Produtos com consumo mais intermitente e demanda média mais baixa. |

O cluster é identificado pelo algoritmo por um número. Os nomes “demanda frequente” e “demanda intermitente” são interpretações feitas após comparar as características médias de cada grupo; não são categorias fornecidas previamente ao K-Means.

### Visualização com PCA e dashboard

O PCA (Análise de Componentes Principais) foi utilizado para representar os produtos em duas dimensões no gráfico. As duas componentes selecionadas representam, em conjunto, aproximadamente 91,68% da variância das características padronizadas. O PCA é empregado nessa etapa para visualização; o K-Means é treinado com as seis características selecionadas para o agrupamento.

A página `/analise/` apresenta indicadores do experimento, um gráfico de dispersão dos produtos por cluster e uma tabela com as características de cada produto. A camada Django prepara os dados e encaminha o resultado ao template; o Chart.js constrói o gráfico no navegador. Os arquivos específicos de estilo e comportamento da página ficam em `static/css/analise.css` e `static/js/analise.js`.

Para acessar o painel localmente, inicie o servidor Django e abra `http://127.0.0.1:8000/analise/`.

---

## Como rodar LOCALMENTE (usando PostgreSQL, não SQLite)

A aplicação lê as configurações via variáveis de ambiente (.env). O banco local é configurado pela variável `DATABASE_URL`.

1) Clonar o repositório

```bat
git clone https://github.com/galimarodrigues/controle-de-estoque.git
cd controle-de-estoque
```

2) Criar e ativar o ambiente virtual

- Windows (cmd):
```bat
py -3 -m venv venv
venv\Scripts\activate
```
- Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

3) Instalar dependências
```bash
python -m pip install -r requirements.txt
```

O `requirements.txt` inclui as dependências utilizadas pelo módulo de análise de dados, incluindo `pandas`, `numpy` e `scikit-learn`.

4) Instalar e iniciar o PostgreSQL
- Baixe e instale: https://www.postgresql.org/download/
- Guarde a senha do usuário `postgres` definida na instalação (porta padrão: 5432).
- (Windows) Para usar o `psql` no terminal, adicione o diretório `bin` do PostgreSQL ao PATH.

5) Criar o banco de dados local
- Via terminal (psql):
```bat
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE estoque_db;"
```
- Via pgAdmin: Databases → Create → Database… → Name: `estoque_db`.

6) Configurar variáveis de ambiente (.env)
- Copie o exemplo e ajuste conforme suas credenciais locais:
```bat
copy .env.example .env
```
- Edite `.env` e garanta algo como:
```
SECRET_KEY=dev-change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1,http://localhost
DATABASE_URL=postgres://postgres:SUASENHA@localhost:5432/estoque_db
```
Obs.: Troque `SUASENHA` pela senha do usuário postgres que você definiu.

7) Aplicar migrações e (opcional) criar superusuário
```bash
python manage.py migrate
python manage.py createsuperuser
```

8) Carregar os dados de demonstração (opcional)

O projeto contém scripts de seed que carregam categorias, produtos e movimentações a partir dos arquivos JSON. Para verificar o que seria carregado sem gravar alterações, execute primeiro:

```powershell
python scripts\seed_prod_v2.py --mode orm --dry-run
```

Se o resultado estiver correto e você desejar popular o banco local, execute:

```powershell
python scripts\seed_prod_v2.py --mode orm
```

O modo `orm` utiliza o banco configurado pelo Django. Faça a carga somente no banco correto e evite executá-la em produção sem verificar previamente o conteúdo e o efeito do seed.

9) Rodar o servidor de desenvolvimento
```bash
python manage.py runserver
```
Acesse: http://127.0.0.1:8000/

Para abrir o painel de análise, acesse: http://127.0.0.1:8000/analise/

---

## Deploy na Railway

Este projeto já está pronto para deploy na Railway usando `Procfile`, `dj-database-url` e variáveis de ambiente. Passos resumidos:

1) Subir o código para o GitHub (público ou privado)

2) Criar o projeto na Railway
- Acesse https://railway.app
- New Project → Deploy from GitHub → selecione este repositório.

3) Adicionar o PostgreSQL na Railway
- No projeto, adicione o Add-on: PostgreSQL.
- A Railway criará a variável `DATABASE_URL` automaticamente apontando para o banco.

4) Configurar variáveis de ambiente na Railway
- Em Settings → Variables, configure:
  - `SECRET_KEY` = uma chave forte e secreta
  - `DEBUG` = `False`
  - `ALLOWED_HOSTS` = `.up.railway.app,seu-dominio.com,www.seu-dominio.com`
  - `CSRF_TRUSTED_ORIGINS` = `https://<seu-subdominio>.up.railway.app,https://seu-dominio.com,https://www.seu-dominio.com`
  - `DATABASE_URL` = já fornecida pelo add-on de Postgres

5) Deploy
- Abra a aba Deploy e aguarde a publicação.
- O `Procfile` executa automaticamente: migrações, coleta de estáticos e inicia o Gunicorn:
  - `python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn cafeteria.wsgi:application --bind 0.0.0.0:$PORT`

6) Acessar
- Use a URL pública mostrada na Railway (ex.: `https://<app>.up.railway.app`).

Dica: Para criar um superusuário em produção, você pode abrir um shell na Railway (ou usar o Deploy tab com um "Run Command") e executar `python manage.py createsuperuser`.

---

## Como a configuração funciona

- `cafeteria/settings.py` utiliza `dj-database-url` e prioriza `DATABASE_URL` (Railway e local). Se `DATABASE_URL` não estiver setada, cai para SQLite apenas como fallback. Como aqui queremos Postgres local, mantenha `DATABASE_URL` definida no seu `.env`.
- Estáticos em produção são servidos via WhiteNoise (`STATIC_ROOT` + `collectstatic`).
- Os arquivos de estilo e JavaScript da análise ficam em `static/css/analise.css` e `static/js/analise.js`; o Django disponibiliza esses arquivos pelo sistema de arquivos estáticos.
- Segurança:
  - `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` devem incluir seus domínios.
  - Em produção (`DEBUG=False`), cookies e redirecionamento para HTTPS estão habilitados.

---

## Solução de problemas

- DisallowedHost: adicione seu domínio em `ALLOWED_HOSTS`.
- Erros de CSRF em produção: defina `CSRF_TRUSTED_ORIGINS` com o esquema (`https://`), incluindo o domínio da Railway.
- Erro de conexão ao Postgres local: confirme usuário/senha/porta, se o serviço está ativo e se `DATABASE_URL` está correto.
- Arquivos estáticos 404 em produção: confira logs da `collectstatic`; o `Procfile` já roda `collectstatic` a cada deploy.
- Erro ao importar `pandas`, `numpy` ou `sklearn`: confirme que o ambiente virtual está ativo e execute `python -m pip install -r requirements.txt`.
- Gráfico vazio no painel de análise: confirme que o template usa os dados de clusters enviados pela view e que os arquivos `static/js/analise.js` e `static/css/analise.css` estão sendo carregados.

---

## Estrutura do projeto
```
controle-de-estoque/
├── manage.py
├── Procfile
├── requirements.txt
├── runtime.txt
├── cafeteria/
│   └── settings.py
├── estoque/
├── consulta/
├── analise/
│   ├── services.py       # preparação do dataset
│   ├── ml.py             # experimentos de previsão
│   └── clustering.py     # K-Means e PCA
├── scripts/
│   ├── seed_prod.py
│   ├── seed_prod_v2.py
│   └── seed/
│       ├── estoque_categoria.json
│       ├── estoque_produto.json
│       └── estoque_movimentacao.json
├── static/
│   ├── css/
│   │   ├── styles.css
│   │   └── analise.css
│   └── js/
│       ├── scripts.js
│       └── analise.js
└── templates/
    ├── base.html
    └── analise.html
```
