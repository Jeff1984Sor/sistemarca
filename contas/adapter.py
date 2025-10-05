# em contas/adapter.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """
        Chamado quando um usuário loga com uma conta social.
        Garante que o primeiro nome e o sobrenome sejam salvos.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Pega os dados extras fornecidos pela Microsoft
        extra_data = sociallogin.account.extra_data
        
        first_name = extra_data.get('givenName')
        last_name = extra_data.get('surname')

        if first_name and not user.first_name:
            user.first_name = first_name
        if last_name and not user.last_name:
            user.last_name = last_name

        user.save()
        return user