# Controle de Estoque - Cafeteria

Aplicação Django para controle de estoque de uma cafeteria. Suporta execução local com PostgreSQL e deploy em produção via Railway.

## Tecnologias
- Python 3.10+
- Django
- PostgreSQL
- Bootstrap 5
- WhiteNoise (estáticos em produção)

## Requisitos
- Python 3.10+
- PostgreSQL 13+
- Git

Opcional (GUI): pgAdmin.

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
pip install -r requirements.txt
```

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

8) Rodar o servidor de desenvolvimento
```bash
python manage.py runserver
```
Acesse: http://127.0.0.1:8000/

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
- Segurança:
  - `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` devem incluir seus domínios.
  - Em produção (`DEBUG=False`), cookies e redirecionamento para HTTPS estão habilitados.

---

## Solução de problemas

- DisallowedHost: adicione seu domínio em `ALLOWED_HOSTS`.
- Erros de CSRF em produção: defina `CSRF_TRUSTED_ORIGINS` com o esquema (`https://`), incluindo o domínio da Railway.
- Erro de conexão ao Postgres local: confirme usuário/senha/porta, se o serviço está ativo e se `DATABASE_URL` está correto.
- Arquivos estáticos 404 em produção: confira logs da `collectstatic`; o `Procfile` já roda `collectstatic` a cada deploy.

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
├── static/
└── templates/
```
