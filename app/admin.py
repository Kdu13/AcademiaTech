from django.contrib import admin
from .models import Categoria, ItemPedido, Pedido, Servico

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "descricao")
    ordering = ("nome",)

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ["nome", "preco", "categoria", "ativo", "atualizado_em"]
    list_filter = ["categoria", "ativo"]
    search_fields = ["nome", "descricao"]
    ordering = ["nome", "preco"]
    list_per_page = 25


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ("preco_unitario",)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "status", "criado_em", "atualizado_em")
    list_filter = ("status", "criado_em")
    search_fields = ("usuario__username", "usuario__email")
    inlines = (ItemPedidoInline,)
