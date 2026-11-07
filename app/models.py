from decimal import Decimal

from django.conf import settings
from django.db import models

class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class Servico(models.Model):
    nome = models.CharField(max_length=150, verbose_name="nome do curso")
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="preço (R$)")
    imagem = models.URLField(blank=True, default="", verbose_name="URL da imagem")
    ativo = models.BooleanField(default=True, verbose_name="ativo")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='servicos', blank=True, null=True)

    class Meta:
        verbose_name = "curso"
        verbose_name_plural = "cursos"

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    class Status(models.TextChoices):
        CARRINHO = "carrinho", "Carrinho"
        REALIZADO = "realizado", "Realizado"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pedidos",
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.CARRINHO,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return sum((item.subtotal for item in self.itens.all()), Decimal("0.00"))

    def __str__(self):
        return f"Pedido #{self.pk} - {self.usuario.username}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    servico = models.ForeignKey(
        Servico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itens_pedido",
    )
    nome_servico = models.CharField(max_length=150)
    imagem_url = models.URLField(blank=True, default="")
    quantidade = models.PositiveIntegerField(default=1)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("pedido", "servico"),
                name="pedido_servico_unico",
            )
        ]

    def save(self, *args, **kwargs):
        if self.servico_id and not self.imagem_url:
            self.imagem_url = self.servico.imagem or ""
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.preco_unitario * self.quantidade

    def __str__(self):
        return f"{self.quantidade} x {self.nome_servico}"
