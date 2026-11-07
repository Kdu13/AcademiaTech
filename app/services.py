from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import requests
from django.conf import settings
from django.core.cache import cache


TAXA_CACHE_KEY = "academia_tech_usd_brl_rate"
EQUIPAMENTOS_CACHE_KEY = "academia_tech_partner_equipment_v1"
TAXA_CACHE_SECONDS = 60 * 60
EQUIPAMENTOS_CACHE_SECONDS = 20 * 60
EQUIPAMENTOS_ENDPOINTS = (
    ("Laptops", "https://dummyjson.com/products/category/laptops"),
    ("Smartphones", "https://dummyjson.com/products/category/smartphones"),
    ("Tablets", "https://dummyjson.com/products/category/tablets"),
)


def _decimal(valor):
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def get_usd_brl_rate():
    taxa_cache = cache.get(TAXA_CACHE_KEY)
    if taxa_cache:
        return _decimal(taxa_cache)

    try:
        resposta = requests.get(
            "https://economia.awesomeapi.com.br/last/USD-BRL",
            timeout=6,
        )
        resposta.raise_for_status()
        taxa = Decimal(str(resposta.json()["USDBRL"]["bid"]))
        if taxa <= 0:
            raise ValueError("A cotação recebida é inválida.")
    except (requests.RequestException, ValueError, KeyError, TypeError, InvalidOperation):
        taxa = _decimal(getattr(settings, "USD_BRL_FALLBACK", 5.50))

    cache.set(TAXA_CACHE_KEY, str(taxa), TAXA_CACHE_SECONDS)
    return taxa


def converter_para_brl(valor_usd):
    return (_decimal(valor_usd) * get_usd_brl_rate()).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def formatar_brl(valor):
    valor_formatado = f"{_decimal(valor):,.2f}"
    return "R$ " + valor_formatado.replace(",", "#").replace(".", ",").replace("#", ".")


def get_equipamentos_parceiros():
    cacheado = cache.get(EQUIPAMENTOS_CACHE_KEY)
    if cacheado is not None:
        return cacheado

    produtos = []
    falhas = 0
    taxa = get_usd_brl_rate()

    for categoria, url in EQUIPAMENTOS_ENDPOINTS:
        try:
            resposta = requests.get(url, timeout=8)
            resposta.raise_for_status()
            dados = resposta.json()
            lista = dados.get("products", []) if isinstance(dados, dict) else []
            if not isinstance(lista, list):
                raise ValueError("Resposta inválida da API de equipamentos.")

            for produto in lista:
                if not isinstance(produto, dict):
                    continue
                preco_usd = _decimal(produto.get("price"))
                imagens = produto.get("images") or []
                imagem = produto.get("thumbnail") or (imagens[0] if imagens else "")
                produtos.append({
                    "id": produto.get("id"),
                    "title": produto.get("title", "Equipamento"),
                    "description": produto.get("description", ""),
                    "image": imagem,
                    "category": categoria,
                    "price_brl": (preco_usd * taxa).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    ),
                    "price_brl_text": formatar_brl(preco_usd * taxa),
                })
        except (requests.RequestException, ValueError, TypeError, InvalidOperation, AttributeError):
            falhas += 1

    api_erro = falhas > 0
    resultado = (produtos, api_erro)
    validade = 120 if falhas == len(EQUIPAMENTOS_ENDPOINTS) else EQUIPAMENTOS_CACHE_SECONDS
    cache.set(EQUIPAMENTOS_CACHE_KEY, resultado, validade)
    return resultado
