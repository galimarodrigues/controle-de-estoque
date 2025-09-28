# Controle de Estoque - Cafeteria

Este é um projeto de controle de estoque para uma cafeteria, desenvolvido em Python com Django, utilizando PostgreSQL como banco de dados. O objetivo deste projeto é gerenciar o estoque de produtos (como café, salgados, refrigerantes) e controlar a entrada e saída desses produtos.

#### Projeto Integrador - UNIVESP (Universidade Virtual do Estado de São Paulo)
Este projeto foi desenvolvido como parte da disciplina de Projeto Integrador da UNIVESP (Universidade Virtual do Estado de São Paulo), cujo tema é:

    "Desenvolvimento de um software com framework web que utilize noções de banco de dados, praticando controle de versão."

O Projeto Integrador tem como objetivo propor uma solução tecnológica para um problema real de uma empresa, instituição pública, ONG ou comunidade. Neste caso, a aplicação foi pensada como uma ferramenta de apoio à gestão de estoque de uma cafeteria, podendo ser adaptada a diversos outros tipos de estabelecimentos com necessidades semelhantes.

## Tecnologias Utilizadas

- Python
- Django
- Bootstrap
- PostgreSQL
- Git
- GitHub

## Pré-Requisitos

Antes de começar, você precisa ter instalado em sua máquina:

- Python 3.8+ — https://www.python.org/downloads/
- PostgreSQL 13+ — https://www.postgresql.org/download/
- Git — https://git-scm.com/

## Passos para Rodar o Projeto

Siga os passos abaixo para configurar o projeto em sua máquina.

### 1. Clonar o Repositório

```bash
git clone git@github.com:galimarodrigues/controle-de-estoque.git
cd controle-de-estoque
```

### 2. Criar e Ativar o Ambiente Virtual

- Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

- Windows (cmd):
```bat
py -3 -m venv venv
.\venv\Scripts\activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Instalar e Preparar o PostgreSQL

1) Instale o PostgreSQL a partir do site oficial. Durante a instalação, anote a senha do usuário padrão "postgres". A porta padrão é 5432.

2) (Windows) Adicione o PostgreSQL ao PATH para poder usar o comando `psql` no terminal:
- Caminho típico: `C:\\Program Files\\PostgreSQL\\<versão>\\bin`
- Passos: Configurações do Windows → Sistema → Sobre → Configurações avançadas do sistema → Variáveis de Ambiente → selecione `Path` → Editar → Novo → cole o caminho do `bin` do PostgreSQL → OK.
- Valide em um novo terminal:
```bat
psql --version
```

3) Crie o banco de dados do projeto (escolha uma opção):
- Via terminal (psql):
```bat
psql -U postgres -h localhost -c "CREATE DATABASE estoque_db;"
```
- Via pgAdmin: abra o pgAdmin, conecte em localhost, clique com o botão direito em Databases → Create → Database… → Nome: `estoque_db`.

### 5. Configurar o Banco no Django (`cafeteria/settings.py`)

Confirme/ajuste a configuração do banco conforme abaixo (altere a senha conforme a sua instalação):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'estoque_db',
        'USER': 'postgres',
        'PASSWORD': 'admin',  # ajuste para a sua senha
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 6. Rodar as Migrações

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Criar Superusuário (opcional, para acessar o admin)

```bash
python manage.py createsuperuser
```

### 8. Rodar o Servidor de Desenvolvimento

```bash
python manage.py runserver
```

A aplicação estará disponível em http://127.0.0.1:8000/.

## Observações sobre a migração (MySQL → PostgreSQL)

- Os dados do MySQL não são transferidos automaticamente. Se necessário, recrie categorias e produtos manualmente na interface web ou use um processo de exportação/importação.
- Certifique-se de que o `psycopg2-binary` está instalado (já listado no `requirements.txt`).

## Solução de Problemas

- `psql` não é reconhecido: adicione o diretório `bin` do PostgreSQL ao `PATH` (veja a seção 4.2) e abra um novo terminal.
- Erro de conexão (OperationalError): verifique usuário, senha, host/porta e se o serviço PostgreSQL está em execução.
- Problemas em migrações: execute novamente `python manage.py makemigrations` e `python manage.py migrate`; verifique conflitos em apps.

### Estrutura do Projeto
```
controle-de-estoque/
│
├── manage.py                  # Arquivo principal do Django
├── requirements.txt           # Dependências do projeto
│
├── cafeteria/                 # Configurações do projeto Django
│   └── settings.py            # Configuração do banco e apps
│
├── estoque/                   # App de controle de estoque
│   ├── migrations/            # Migrações do banco de dados
│   ├── models.py              # Modelos de banco de dados
│   ├── views.py               # Lógica das views
│   └── urls.py                # URLs do app
│
├── templates/                 # Templates Django (HTML)
├── static/                    # Arquivos estáticos (CSS, JS, imagens)
└── venv/                      # Ambiente virtual (local)
```
