# configuracoes/context_processors.py
from .models import Modulo, LogoConfig, Tema

def modulos_visiveis(request):
    # Começa com um conjunto vazio
    slugs_permitidos = set()

    # Só continua se o usuário estiver logado
    if request.user.is_authenticated:
        
        # Pega os grupos aos quais o usuário pertence
        grupos_do_usuario = request.user.groups.all()
        
        # Se o usuário pertencer a algum grupo
        if grupos_do_usuario.exists():
            # Pega todos os módulos que estão ligados a QUALQUER um dos grupos do usuário
            modulos_permitidos = Modulo.objects.filter(
                ativo=True,
                grupos_permitidos__in=grupos_do_usuario
            ).distinct()
            slugs_permitidos = set(modulos_permitidos.values_list('slug', flat=True))

    return {'modulos_visiveis': slugs_permitidos}

def logo_processor(request):
    """
    Disponibiliza a URL do logo ativo para todos os templates.
    """
    logo_url = None
    try:
        # Pega o primeiro (e único) logo marcado como 'ativo'
        logo_config = LogoConfig.objects.get(ativo=True)
        if logo_config.logo:
            logo_url = logo_config.logo.url
    except LogoConfig.DoesNotExist:
        pass
        
    return {'logo_url_global': logo_url}

def tema_processor(request):
    """
    Disponibiliza o tema ativo para todos os templates.
    """
    tema_ativo = None
    try:
        tema_ativo = Tema.objects.get(ativo=True)
    except Tema.DoesNotExist:
        # Se nenhum tema estiver no banco, cria um com os valores padrão
        tema_ativo = Tema.objects.create()
        
    return {'tema_ativo': tema_ativo}