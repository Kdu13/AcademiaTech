from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Contato


class ContatoViewTests(TestCase):
    def test_envio_de_contato_salva_e_redireciona(self):
        response = self.client.post(
            reverse("novo_contato"),
            {
                "nome": "Carlos",
                "email": "carlos@example.com",
                "telefone": "11999999999",
                "mensagem": "Mensagem de teste",
            },
        )

        self.assertRedirects(response, reverse("novo_contato"))
        self.assertEqual(Contato.objects.count(), 1)

    def test_formulario_de_contato_carrega(self):
        response = self.client.get(reverse("novo_contato"))
        self.assertEqual(response.status_code, 200)

    def test_caixa_de_entrada_exige_administrador(self):
        contato = Contato.objects.create(
            nome="Ana",
            email="ana@example.com",
            mensagem="Olá",
        )
        response = self.client.get(reverse("lista_contatos"))
        self.assertEqual(response.status_code, 302)

        admin = User.objects.create_superuser(
            username="admin_contatos",
            email="admin@example.com",
            password="SenhaForte-2026",
        )
        self.client.force_login(admin)
        response = self.client.get(reverse("lista_contatos"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ana@example.com")

        response = self.client.post(reverse("excluir_contato", args=[contato.id]))
        self.assertRedirects(response, reverse("lista_contatos"))
        self.assertFalse(Contato.objects.filter(pk=contato.pk).exists())
