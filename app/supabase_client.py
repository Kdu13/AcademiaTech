"""Cliente Supabase para as operações de integrantes.

As credenciais são lidas do arquivo .env na raiz do projeto. A conexão é criada
sob demanda para que o restante do Django continue inicializando sem essas
credenciais configuradas.
"""

from functools import lru_cache

from django.conf import settings
from supabase import create_client


@lru_cache(maxsize=1)
def get_supabase():
    supabase_url = settings.SUPABASE_URL
    # Esta chave secreta fica somente no servidor. As views validam o papel do usuário.
    supabase_key = settings.SUPABASE_KEY

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "Configure SUPABASE_URL e SUPABASE_KEY no ambiente do servidor."
        )

    return create_client(supabase_url, supabase_key)
