import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from app.models import Categoria, Servico
from login.models import Perfil


CATEGORIAS = {
    "Programação": "Desenvolvimento de software, linguagens e aplicações web.",
    "Design": "Design de interfaces, experiência do usuário e prototipação.",
    "Dados": "Análise, visualização e tratamento de dados.",
    "Infraestrutura": "Redes, nuvem, sistemas e infraestrutura de tecnologia.",
}

CURSOS = [
    {
        "nome": "Python do Zero",
        "descricao": "Aprenda lógica, Python e automação com exercícios e projetos guiados.",
        "preco": "129.90",
        "categoria": "Programação",
        "imagem": "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "nome": "Django na Prática",
        "descricao": "Crie aplicações web completas com Django, banco de dados e autenticação.",
        "preco": "179.90",
        "categoria": "Programação",
        "imagem": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "nome": "UI/UX Design",
        "descricao": "Planeje interfaces acessíveis, protótipos e experiências digitais.",
        "preco": "149.90",
        "categoria": "Design",
        "imagem": "https://images.unsplash.com/photo-1558655146-9f40138edfeb?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "nome": "Análise de Dados com Excel",
        "descricao": "Organize dados, crie indicadores e apresente análises com clareza.",
        "preco": "119.90",
        "categoria": "Dados",
        "imagem": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "nome": "Redes e Infraestrutura",
        "descricao": "Conheça os fundamentos de redes, servidores e serviços em nuvem.",
        "preco": "169.90",
        "categoria": "Infraestrutura",
        "imagem": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1000&q=85",
    },
    {
        "nome": "JavaScript para Web",
        "descricao": "Adicione interatividade às páginas e construa aplicações no navegador.",
        "preco": "99.90",
        "categoria": "Programação",
        "imagem": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&w=1000&q=85",
    },
]


class Command(BaseCommand):
    help = "Cria categorias, cursos e, com senha configurada, um cliente de demonstração."

    def add_arguments(self, parser):
        parser.add_argument(
            "--senha-cliente-demo",
            dest="senha_cliente_demo",
            help="Senha inicial do cliente_demo (ou use ACADEMIA_DEMO_PASSWORD).",
        )

    def handle(self, *args, **options):
        categorias = {}
        for nome, descricao in CATEGORIAS.items():
            categoria, _ = Categoria.objects.get_or_create(
                nome=nome,
                defaults={"descricao": descricao, "ativo": True},
            )
            categorias[nome] = categoria

        cursos_criados = 0
        for dados in CURSOS:
            categoria = categorias[dados["categoria"]]
            _, criado = Servico.objects.get_or_create(
                nome=dados["nome"],
                defaults={
                    "descricao": dados["descricao"],
                    "preco": dados["preco"],
                    "categoria": categoria,
                    "imagem": dados["imagem"],
                    "ativo": True,
                },
            )
            cursos_criados += int(criado)

        self.stdout.write(self.style.SUCCESS(
            f"Categorias verificadas: {len(categorias)}. Cursos novos: {cursos_criados}."
        ))

        senha = options.get("senha_cliente_demo") or os.getenv("ACADEMIA_DEMO_PASSWORD")
        if not senha:
            self.stdout.write(
                "Cliente de demonstração não criado. Informe --senha-cliente-demo "
                "ou defina ACADEMIA_DEMO_PASSWORD."
            )
            return

        user_model = get_user_model()
        usuario, criado = user_model.objects.get_or_create(
            username="cliente_demo",
            defaults={
                "email": "cliente.demo@academiatech.local",
                "is_staff": False,
                "is_superuser": False,
            },
        )
        if criado:
            usuario.set_password(senha)
            usuario.save(update_fields=["password"])
        Perfil.objects.get_or_create(usuario=usuario, defaults={"tipo_usuario": "cliente"})
        self.stdout.write(self.style.SUCCESS(
            "Cliente de demonstração disponível: cliente_demo / "
            + ("senha configurada nesta execução." if criado else "conta existente preservada.")
        ))
