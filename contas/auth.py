# contas/auth.py

from django_auth_adfs.backend import AdfsAuthCodeBackend
import requests
from django.core.files.base import ContentFile

class CustomAdfsAuthCodeBackend(AdfsAuthCodeBackend):
    def authenticate(self, request, authorization_code=None, **kwargs):
        # 1. Deixa a biblioteca fazer a autenticação normal primeiro
        user = super().authenticate(request, authorization_code=authorization_code, **kwargs)
        
        # 2. Se a autenticação foi bem-sucedida e temos um usuário...
        if user:
            # 3. Pega o token de acesso que foi usado para o login
            token = request.session.get("adfs_access_token")
            if token:
                # 4. Usa o token para buscar a foto do usuário no Microsoft Graph
                headers = {'Authorization': f'Bearer {token}'}
                # A API retorna a foto em seu tamanho original
                endpoint = "https://graph.microsoft.com/v1.0/me/photo/$value"
                
                photo_response = requests.get(endpoint, headers=headers)
                
                # 5. Se a foto foi encontrada, salva no nosso modelo Perfil
                if photo_response.status_code == 200:
                    # 'photo_response.content' contém os bytes da imagem
                    photo_content = ContentFile(photo_response.content)
                    
                    # Gera um nome de arquivo único para a foto
                    file_name = f'perfil_{user.username}.jpg'
                    
                    # Salva a imagem no campo 'foto' do perfil do usuário
                    user.perfil.foto.save(file_name, photo_content, save=True)
        
        return user