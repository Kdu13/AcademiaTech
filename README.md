# AcademiaTech

A AcademiaTech é uma plataforma web de cursos de tecnologia, desenvolvida como projeto final de WEB III. O sistema permite consultar cursos, 
criar uma conta, realizar pedidos e gerenciar as informações da plataforma.

## Acesse o projeto

[Visitar a AcademiaTech]: https://academiatech.onrender.com/

## Funcionalidades

- Catálogo de cursos organizado por categorias.
- Cadastro, login e gerenciamento de usuários.
- Controle de acesso às áreas administrativas.
- Criação e consulta de pedidos.
- Formulário para envio de mensagens de contato.
- Gerenciamento dos integrantes da equipe.
- Cadastro e gerenciamento de imagens.
- Relatórios administrativos.
- Consulta de produtos de uma API externa.

## Tecnologias

- Python
- Django
- Django REST Framework
- HTML, CSS e JavaScript
- SQLite para desenvolvimento local
- PostgreSQL do Supabase para o ambiente online
- Supabase Storage para armazenamento de imagens
- Render para hospedagem

## Executar localmente

### Requisitos

- Python 3.12 ou superior
- Git

### Linux

Clone o repositório e entre na pasta do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Configure as variáveis no arquivo `.env` e depois execute:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/` no navegador. Para encerrar, pressione `Ctrl+C` e execute `deactivate` para sair do ambiente virtual.

### Windows — PowerShell

Clone o repositório e entre na pasta:

```powershell
git clone https://github.com/Kdu13/AcademiaTech.git
cd AcademiaTech
```

Crie e ative o ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, execute este comando e tente novamente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Instale as dependências e crie o arquivo de configuração:

```powershell
py -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure as variáveis no arquivo `.env` e depois execute:

```powershell
py manage.py migrate
py manage.py createsuperuser
py manage.py runserver
```

Acesse `http://127.0.0.1:8000/` no navegador. Para encerrar, pressione `Ctrl+C` e execute `deactivate` para sair do ambiente virtual.

## Configuração

Consulte `.env.example` para ver as variáveis necessárias. Não publique o arquivo `.env`, senhas ou chaves secretas no GitHub.

## Banco de dados e imagens

No desenvolvimento local, o projeto utiliza o banco local configurado. No ambiente online, utiliza o banco remoto do Supabase. As imagens são armazenadas no Supabase Storage; use o endereço público da imagem no campo correspondente do sistema.
```markdown
