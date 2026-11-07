# Publicação da Academia Tech no PythonAnywhere

Este projeto mantém o SQLite para desenvolvimento local, usa PostgreSQL remoto por `DATABASE_URL` na publicação, e conecta ao Supabase para a equipe e as imagens dos cursos. O deploy é manual no PythonAnywhere.

## 1. Preparar o Supabase

No painel SQL do Supabase, execute uma vez:

1. `supabase/seguranca-integrantes.sql`
2. `supabase/storage-servicos.sql`

Confirme que existe a tabela `public.integrantes` e que o bucket público `cursos` aceita JPG, PNG e WEBP até 2 MB. Em **Connect**, copie a URI PostgreSQL do **Session Pooler** para `DATABASE_URL`. Em **Project Settings > API**, copie a URL e a chave secreta do servidor para `SUPABASE_URL` e `SUPABASE_KEY`. A chave fica somente no arquivo de ambiente do servidor.

## 2. Enviar o código

Envie a pasta do projeto para sua conta PythonAnywhere, por Git ou pelo painel **Files**. Não envie `.env`, `.venv`, `.venv-linux`, `db.sqlite3` ou `media`.

Abra um Bash console no PythonAnywhere e, dentro da pasta que contém `manage.py`, crie o ambiente e instale as dependências:

```bash
python3.12 -m venv ~/.virtualenvs/academia-tech
source ~/.virtualenvs/academia-tech/bin/activate
cd ~/academia-tech
python -m pip install --upgrade pip
python -m pip install -r requirements-prod.txt
```

Se o nome ou caminho enviado for diferente de `~/academia-tech`, use sua pasta real nos comandos seguintes.

## 3. Configurar variáveis

Crie um `.env` na mesma pasta de `manage.py`. Gere uma chave Django segura em um console:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Use estes nomes no `.env` e substitua cada valor de exemplo:

```dotenv
DJANGO_SECRET_KEY=cole-a-chave-gerada
DJANGO_DEBUG=False
ALLOWED_HOSTS=seuusuario.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://seuusuario.pythonanywhere.com
DATABASE_URL=postgresql://usuario:senha@host:porta/banco?sslmode=require
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=chave-secreta-do-servidor
SUPABASE_BUCKET=cursos
USD_BRL_FALLBACK=5.50
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=seu-servidor-smtp
EMAIL_PORT=587
EMAIL_HOST_USER=seu-usuario-smtp
EMAIL_HOST_PASSWORD=sua-senha-smtp
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Academia Tech <seu-email-validado>
ACADEMIA_DEMO_PASSWORD=defina-uma-senha-temporaria-forte
```

`DATABASE_URL` deve ser a URI PostgreSQL do Supabase, com a senha do banco e SSL. Sem ela, o projeto usa SQLite. Não reutilize a chave Django de exemplo nem a senha do cliente de demonstração em uma conta real.

## 4. Criar banco e dados iniciais

Ainda com o ambiente virtual ativo e o `.env` já configurado:

```bash
python manage.py migrate
python manage.py popular_academia_tech
python manage.py createsuperuser
python manage.py check --deploy
python manage.py collectstatic --noinput
```

O comando cria as categorias e cursos de exemplo. Se `ACADEMIA_DEMO_PASSWORD` estiver configurada, também cria `cliente_demo`; se já existir, a conta é preservada. A redefinição de senha usa o SMTP configurado acima.

## 5. Configurar o Web app

1. Na aba **Web**, crie um app com **Manual configuration** e Python 3.12.
2. Em **Virtualenv**, informe `/home/seuusuario/.virtualenvs/academia-tech`.
3. Edite o arquivo WSGI disponibilizado pela aba Web. Ajuste o caminho da pasta do projeto:

```python
import os
import sys
from dotenv import load_dotenv

project_dir = "/home/seuusuario/academia-tech"
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

load_dotenv(os.path.join(project_dir, ".env"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projeto.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

4. Na seção **Static files**, crie o mapeamento `/static/` para `/home/seuusuario/academia-tech/staticfiles`.
5. Salve o WSGI e clique em **Reload** na aba Web.
6. Abra `https://seuusuario.pythonanywhere.com/` e confira também `/admin/`.

Após alterar CSS ou outros arquivos estáticos, rode novamente `collectstatic` e recarregue o Web app.

## 6. Verificações após a publicação

- Cadastre um cliente pelo link **Entrar > Novo usuário**, entre e teste **Dashboard**, **Editar perfil**, **Alterar senha**, **Produtos** e **Meus pedidos**.
- Entre no `/admin/` com o superusuário e confira Cursos, Categorias, Contatos, Pedidos e Perfis.
- Em Produtos, confira cursos locais, equipamentos externos e valores em reais.
- Teste o formulário público Contato; confira e exclua a mensagem pelo painel administrativo do site.
- Teste Equipe/Quem Somos e o envio de uma imagem de curso para o bucket `cursos`.
- No PythonAnywhere, consulte os links **Error log** e **Server log** na aba Web se uma tela falhar.

## Observação sobre plano PythonAnywhere

O acesso a PostgreSQL externo e a conexões de internet sem restrição depende de um plano pago no PythonAnywhere. Em contas gratuitas, a lista de destinos externos permitidos pode impedir o acesso ao Supabase, DummyJSON e AwesomeAPI; SQLite também não é recomendado pelo próprio provedor para produção. Confirme o plano e o acesso de rede antes de publicar.
