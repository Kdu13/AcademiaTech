from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from .models import Perfil


class LoginViewTests(TestCase):
    def test_cadastro_cria_usuario_e_perfil(self):
        response = self.client.post(
            reverse("cadastro"),
            {
                "username": "usuario_teste",
                "email": "usuario@example.com",
                "password1": "UmaSenhaForte-2040",
                "password2": "UmaSenhaForte-2040",
            },
        )

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="usuario_teste")
        self.assertEqual(Perfil.objects.get(usuario=user).tipo_usuario, "cliente")

    def test_dashboard_de_usuario_sem_perfil_nao_quebra(self):
        user = User.objects.create_user(username="sem_perfil", password="senha-teste")
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)

    def test_perfil_administrador_nao_promove_conta_a_superusuario(self):
        user = User.objects.create_user(username="admin_perfil", password="SenhaForte-2026")
        Perfil.objects.create(usuario=user, tipo_usuario="administrador")
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_admin_staff_e_redirecionado_para_o_admin_django(self):
        user = User.objects.create_superuser(
            username="admin_staff",
            email="admin_staff@example.com",
            password="SenhaForte-2026",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(response, reverse("admin:index"), fetch_redirect_response=False)

    def test_login_de_admin_ignora_destino_publico_e_abre_admin(self):
        User.objects.create_superuser(
            username="login_admin",
            email="login_admin@example.com",
            password="SenhaForte-2026",
        )

        response = self.client.post(
            reverse("login") + "?next=/produtos/",
            {"username": "login_admin", "password": "SenhaForte-2026"},
        )

        self.assertRedirects(response, reverse("admin:index"), fetch_redirect_response=False)

    def test_painel_admin_exibe_atalhos_para_as_paginas_protegidas(self):
        user = User.objects.create_superuser(
            username="atalhos_admin",
            email="atalhos@example.com",
            password="SenhaForte-2026",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Atalhos da Academia Tech")
        self.assertContains(response, "Equipe")
        self.assertContains(response, "Relatórios")

    def test_recuperacao_de_senha_usa_email_nativo_do_django(self):
        User.objects.create_user(
            username="recuperar",
            email="recuperar@example.com",
            password="SenhaForte-2026",
        )

        response = self.client.post(
            reverse("password_reset"),
            {"email": "recuperar@example.com"},
        )

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("senha/redefinir/", mail.outbox[0].body)

    def test_perfil_exibe_e_atualiza_dados_da_conta(self):
        user = User.objects.create_user(
            username="perfil_teste",
            email="perfil@example.com",
            password="SenhaForte-2026",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("perfil"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Meu perfil")

        response = self.client.post(reverse("perfil"), {
            "first_name": "Ana",
            "last_name": "Silva",
            "email": "ana@example.com",
        })
        self.assertRedirects(response, reverse("perfil"))
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Ana")
        self.assertEqual(user.email, "ana@example.com")
