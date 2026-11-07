from uuid import uuid4
from urllib.parse import unquote, urlparse

from django.conf import settings

from .supabase_client import get_supabase


def upload_imagem_curso(imagem):
    """Envia uma imagem validada pelo servidor e retorna sua URL pública."""
    formatos = {
        "JPEG": ("jpg", "image/jpeg"),
        "PNG": ("png", "image/png"),
        "WEBP": ("webp", "image/webp"),
    }
    formato = getattr(getattr(imagem, "image", None), "format", "")
    if formato not in formatos:
        raise ValueError("Formato de imagem não aceito.")

    extensao, content_type = formatos[formato]
    caminho = f"{uuid4().hex}.{extensao}"
    imagem.seek(0)
    bucket = get_supabase().storage.from_(settings.SUPABASE_BUCKET)
    bucket.upload(
        caminho,
        imagem.read(),
        {"content-type": content_type, "cache-control": "3600", "upsert": "false"},
    )
    return bucket.get_public_url(caminho)


def excluir_imagem_curso(url):
    """Remove somente objetos deste bucket, sem tocar em URLs externas."""
    projeto = urlparse(settings.SUPABASE_URL)
    imagem = urlparse(url or "")
    if not projeto.netloc or imagem.netloc != projeto.netloc:
        return
    prefixo = f"/storage/v1/object/public/{settings.SUPABASE_BUCKET}/"
    if not imagem.path.startswith(prefixo):
        return
    caminho = unquote(imagem.path[len(prefixo):])
    if caminho:
        get_supabase().storage.from_(settings.SUPABASE_BUCKET).remove([caminho])
