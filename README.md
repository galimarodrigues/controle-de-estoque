# Controle de Estoque - Cafeteria

Este é um projeto de controle de estoque para uma cafeteria, desenvolvido em Python com Django, utilizando MySQL como banco de dados. O objetivo deste projeto é gerenciar o estoque de produtos (como café, salgados, refrigerantes) e controlar a entrada e saída desses produtos.

## Tecnologias Utilizadas

- Python
- Django
- MySQL
- Git
- GitHub

## Pré-Requisitos

Antes de começar, você precisa ter instalado em sua máquina:

- [Python 3.8+](https://www.python.org/downloads/)
- [MySQL 5.7+](https://dev.mysql.com/downloads/)
- [Git](https://git-scm.com/)

## Passos para Rodar o Projeto

Siga os passos abaixo para configurar o projeto em sua máquina.

### 1. Clonando o Repositório

Clone o repositório para sua máquina local utilizando o comando Git:

```bash
git clone git@github.com:galimarodrigues/controle-de-estoque.git
```

### 2. Criando o Ambiente Virtual

Após clonar o repositório, acesse o diretório do projeto e crie um ambiente virtual para isolar as dependências do projeto:

```bash
cd controle-de-estoque
python3 -m venv venv
```

### 3. Ativando o Ambiente Virtual

Ative o ambiente virtual criado. O comando varia dependendo do seu sistema operacional:

- Linux / macOS:
```bash
source venv/bin/activate
```

- Windows:
```bash
.\venv\Scripts\activate
```

### 4. Instalando Dependências
Instale as dependências do projeto usando o arquivo requirements.txt:

```bash
pip install -r requirements.txt
```

### 5. Configurando o Banco de Dados
1. ##### Criando o Banco de Dados MySQL:
    Certifique-se de ter o MySQL instalado e em execução. Crie o banco de dados com o nome estoque_db:
    ```bash
    CREATE DATABASE estoque_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    ```

2. ##### Configuração do settings.py:
    No arquivo settings.py do Django, no diretório cafeteria, configure as credenciais do seu banco de dados MySQL:
    ```bash
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'estoque_db',  # Nome do banco de dados
            'USER': 'root',         # Usuário do MySQL
            'PASSWORD': 'root',     # Senha do MySQL
            'HOST': 'localhost',    # Se o MySQL estiver local
            'PORT': '3306',         # Porta padrão do MySQL
        }
    }
    ```

### 6. Rodando as Migrações
Antes de rodar o comando migrate, é importante rodar o comando makemigrations para criar arquivos de migração sempre que você fizer alterações nos modelos (models) do Django.

##### Rodando makemigrations
Para criar os arquivos de migração a partir de qualquer alteração nos modelos:

```bash
python manage.py makemigrations
```

##### Rodando migrate
Agora, rode as migrações para aplicar as alterações no banco de dados:

```bash
python manage.py migrate
```

### 7. Rodando o Servidor de Desenvolvimento
Após realizar as migrações, inicie o servidor de desenvolvimento do Django:

```bash
python manage.py runserver
```

O servidor estará rodando em http://127.0.0.1:8000/.

## Contribuições

Para contribuir com o projeto, siga estas etapas:

1. Faça um fork do repositório.
2. Crie uma branch para sua funcionalidade ou correção.
3. Realize suas modificações e faça o commit.
4. Push para o seu repositório e abra um Pull Request.

Aguarde a aprovação do seu Pull Request antes de integrar suas alterações ao projeto.