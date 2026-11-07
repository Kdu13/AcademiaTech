import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from login.models import Perfil


class Command(BaseCommand):
    help = "Cria o usuário administrador inicial usando variáveis de ambiente."

    def handle(self, *args, **options):
        user_model = get_user_model()
        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
        if not all((username, email, password)):
            if user_model.objects.filter(is_superuser=True).exists():
                self.stdout.write("Administrador já existe; bootstrap ignorado.")
                return
            raise CommandError("Configure as três variáveis DJANGO_SUPERUSER_* para criar o administrador inicial.")

        user, criado = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        if criado:
            user.set_password(password)
        user.email = email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        Perfil.objects.update_or_create(
            usuario=user,
            defaults={"tipo_usuario": "administrador"},
        )
        self.stdout.write(self.style.SUCCESS(f"Administrador {username} disponível."))
