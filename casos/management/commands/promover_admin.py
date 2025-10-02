# casos/management/commands/promover_admin.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Promove um usuário existente a superusuário.'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='O username (geralmente e-mail) do usuário a ser promovido.')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        try:
            user = User.objects.get(username=username)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Sucesso! Usuário "{username}" agora é um superusuário.'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Erro: Usuário "{username}" não encontrado no banco de dados.'))