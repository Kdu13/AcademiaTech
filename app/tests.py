from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from login.models import Perfil
from .models import Categoria, ItemPedido, Pedido, Servico


class ServicoViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.categoria = Categoria.objects.create(nome="Consultoria")
        self.servico = Servico.objects.create(
            nome="Planejamento",
            descricao="Plano inicial",
            preco="250.00",
            imagem="https://example.com/curso.jpg",
            categoria=self.categoria,
        )

    def criar_admin(self):
        admin = User.objects.create_superuser(
            username="admin_teste",
            email="admin@example.com",
            password="SenhaForte-2026",
        )
        self.client.force_login(admin)
        return admin

    def criar_cliente(self):
        cliente = User.objects.create_user(
            username="cliente_teste",
            email="cliente@example.com",
            password="SenhaForte-2026",
        )
        Perfil.objects.create(usuario=cliente, tipo_usuario="cliente")
        return cliente

    def test_lista_servicos_carrega(self):
        self.criar_admin()
        response = self.client.get(reverse("servicos"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planejamento")
        self.assertContains(response, "Cursos da Academia")

    def test_exclusao_de_servico_exige_admin_e_post(self):
        url = reverse("delServico", args=[self.servico.id])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertTrue(Servico.objects.filter(pk=self.servico.pk).exists())

        self.criar_admin()
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url)
        self.assertRedirects(response, reverse("servicos"))
        self.assertFalse(Servico.objects.filter(pk=self.servico.pk).exists())

    def test_cliente_nao_pode_cadastrar_servico(self):
        self.client.force_login(self.criar_cliente())
        response = self.client.get(reverse("addServico"))
        self.assertRedirects(response, reverse("dashboard"))

    def test_api_lista_categorias_e_bloqueia_escrita_publica(self):
        response = self.client.get(reverse("categoriasAPI"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["nome"], "Consultoria")

        response = self.client.post(reverse("categoriasAPI"), {"nome": "Nova"})
        self.assertEqual(response.status_code, 403)

    def test_relatorio_exige_admin_e_exibe_totais(self):
        response = self.client.get(reverse("relatorios"))
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("relatorios"))

        self.criar_admin()
        response = self.client.get(reverse("relatorios"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cursos por categoria")
        self.assertEqual(response.context["servicos_ativos"], 1)

    @patch("app.services.requests.get")
    def test_produtos_mostra_catalogo_local_e_api(self, get):
        def resposta_para_url(url, timeout):
            resposta = Mock()
            resposta.raise_for_status.return_value = None
            if "awesomeapi" in url:
                resposta.json.return_value = {"USDBRL": {"bid": "5.00"}}
            elif "laptops" in url:
                resposta.json.return_value = {"products": [{
                    "id": 42,
                    "title": "Notebook de demonstração",
                    "description": "Equipamento externo",
                    "thumbnail": "https://example.com/item.jpg",
                    "images": [],
                    "price": 12.5,
                }]}
            else:
                resposta.json.return_value = {"products": []}
            return resposta

        get.side_effect = resposta_para_url

        response = self.client.get(reverse("produtos"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planejamento")
        self.assertContains(response, "Notebook de demonstração")
        self.assertContains(response, "R$ 62,50")
        self.assertContains(response, "Valores convertidos de USD para BRL")
        self.assertContains(response, "Entrar para comprar")
        self.assertNotContains(response, 'class="buy-button"')
        self.client.get(reverse("produtos"))
        self.assertEqual(get.call_count, 4)

    @patch("app.services.requests.get", side_effect=requests.Timeout)
    def test_produtos_seguem_abertos_quando_api_externa_falha(self, get):
        response = self.client.get(reverse("produtos"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Equipamentos temporariamente indisponíveis")
        self.assertContains(response, "Planejamento")

    @patch("app.services.requests.get", side_effect=requests.Timeout)
    def test_cotacao_usa_valor_de_fallback_e_formata_moeda(self, get):
        from .services import converter_para_brl, formatar_brl, get_usd_brl_rate

        cache.clear()
        self.assertEqual(get_usd_brl_rate(), Decimal("5.5"))
        self.assertEqual(converter_para_brl("2"), Decimal("11.00"))
        self.assertEqual(formatar_brl("1234.5"), "R$ 1.234,50")
        get.assert_called_once()

    @patch("app.storage.upload_imagem_curso", return_value="https://example.com/novo-curso.webp")
    def test_formulario_de_curso_envia_imagem_e_salva_url(self, upload):
        self.criar_admin()
        conteudo = BytesIO()
        Image.new("RGB", (4, 4), color=(20, 140, 120)).save(conteudo, format="PNG")
        imagem = SimpleUploadedFile(
            "curso.png",
            conteudo.getvalue(),
            content_type="image/png",
        )

        response = self.client.post(reverse("addServico"), {
            "nome": "Curso com imagem",
            "descricao": "Teste de envio",
            "preco": "89.90",
            "categoria": str(self.categoria.pk),
            "ativo": "on",
            "imagem_upload": imagem,
        })

        self.assertRedirects(response, reverse("servicos"))
        self.assertEqual(Servico.objects.get(nome="Curso com imagem").imagem, "https://example.com/novo-curso.webp")
        upload.assert_called_once()

    def test_edicao_de_curso_remove_imagem_se_solicitado(self):
        self.criar_admin()

        response = self.client.post(reverse("editServico", args=[self.servico.pk]), {
            "nome": self.servico.nome,
            "descricao": self.servico.descricao,
            "preco": str(self.servico.preco),
            "categoria": str(self.categoria.pk),
            "ativo": "on",
            "limpar_imagem": "on",
        })

        self.assertRedirects(response, reverse("servicos"))
        self.servico.refresh_from_db()
        self.assertEqual(self.servico.imagem, "")

    def test_cliente_adiciona_remove_e_finaliza_pedido(self):
        cliente = self.criar_cliente()
        self.client.force_login(cliente)
        url_adicionar = reverse("adicionar_ao_carrinho", args=[self.servico.id])

        self.assertEqual(self.client.post(url_adicionar).status_code, 302)
        self.client.post(url_adicionar)
        pedido = Pedido.objects.get(usuario=cliente, status=Pedido.Status.CARRINHO)
        item = ItemPedido.objects.get(pedido=pedido, servico=self.servico)
        self.assertEqual(item.quantidade, 2)
        self.assertEqual(pedido.total, 500)
        self.assertEqual(item.imagem_url, "https://example.com/curso.jpg")

        response = self.client.get(reverse("meus-pedidos"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planejamento")

        self.assertEqual(
            self.client.post(reverse("finalizar_pedido")).status_code,
            302,
        )
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, Pedido.Status.REALIZADO)

    def test_pedido_mantem_historico_se_servico_for_excluido(self):
        cliente = self.criar_cliente()
        pedido = Pedido.objects.create(usuario=cliente)
        ItemPedido.objects.create(
            pedido=pedido,
            servico=self.servico,
            nome_servico=self.servico.nome,
            quantidade=1,
            preco_unitario=self.servico.preco,
        )

        self.criar_admin()
        self.client.post(reverse("delServico", args=[self.servico.id]))

        item = ItemPedido.objects.get(pedido=pedido)
        self.assertIsNone(item.servico)
        self.assertEqual(item.nome_servico, "Planejamento")
        self.assertEqual(item.imagem_url, "https://example.com/curso.jpg")

    def test_cliente_nao_visualiza_pedidos_de_outra_conta(self):
        cliente = self.criar_cliente()
        outro_cliente = User.objects.create_user(
            username="outro_cliente",
            password="SenhaForte-2026",
        )
        pedido = Pedido.objects.create(usuario=outro_cliente)
        ItemPedido.objects.create(
            pedido=pedido,
            servico=self.servico,
            nome_servico="Item privado de outro cliente",
            quantidade=1,
            preco_unitario=self.servico.preco,
        )
        self.client.force_login(cliente)

        response = self.client.get(reverse("meus-pedidos"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Item privado de outro cliente")


class IntegranteViewTests(TestCase):
    def criar_admin(self):
        admin = User.objects.create_superuser(
            username="admin_time",
            email="admin_time@example.com",
            password="SenhaForte-2026",
        )
        self.client.force_login(admin)

    @patch("app.views.get_supabase")
    def test_lista_integrantes(self, get_supabase):
        get_supabase.return_value.table.return_value.select.return_value.order.return_value.execute.return_value = (
            SimpleNamespace(data=[])
        )

        self.criar_admin()
        response = self.client.get(reverse("integrantes"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nenhum integrante cadastrado")

    @patch("app.views.get_supabase")
    def test_cadastro_de_integrante_exige_admin(self, get_supabase):
        response = self.client.post(
            reverse("addIntegrante"),
            {
                "nome": "Ana",
                "cargo": "Designer",
                "biografia": "Biografia de teste",
                "foto": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        get_supabase.assert_not_called()

        self.criar_admin()
        response = self.client.post(
            reverse("addIntegrante"),
            {
                "nome": "Ana",
                "cargo": "Designer",
                "biografia": "Biografia de teste",
                "foto": "",
            },
        )
        self.assertRedirects(response, reverse("integrantes"))
        get_supabase.return_value.table.return_value.insert.assert_called_once_with(
            {
                "nome": "Ana",
                "cargo": "Designer",
                "biografia": "Biografia de teste",
                "foto_url": None,
            }
        )

    @patch("app.views.get_supabase")
    def test_quem_somos_apresenta_institucional_equipe(self, get_supabase):
        get_supabase.return_value.table.return_value.select.return_value.order.return_value.execute.return_value = (
            SimpleNamespace(data=[])
        )
        response = self.client.get(reverse("quem_somos"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tecnologia acessível")

    @patch("app.views.get_supabase")
    def test_edicao_de_integrante_exige_admin_e_atualiza_supabase(self, get_supabase):
        integrante = {
            "id": 8,
            "nome": "Ana",
            "cargo": "Designer",
            "biografia": "Antes",
            "foto_url": None,
        }
        get_supabase.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            SimpleNamespace(data=[integrante])
        )
        url = reverse("editIntegrante", args=[8])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        get_supabase.assert_not_called()

        self.criar_admin()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar integrante")
        response = self.client.post(url, {
            "nome": "Ana Silva",
            "cargo": "Designer de produto",
            "biografia": "Atualizada",
            "foto": "",
        })

        self.assertRedirects(response, reverse("integrantes"))
        get_supabase.return_value.table.return_value.update.assert_called_once_with({
            "nome": "Ana Silva",
            "cargo": "Designer de produto",
            "biografia": "Atualizada",
            "foto_url": None,
        })
