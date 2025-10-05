# configuracoes/context_processors.py (ATUALIZADO E ROBUSTO)

from .models import Modulo, LogoConfig, Tema

def modulos_visiveis(request):
    """
    Disponibiliza um conjunto de slugs de módulos permitidos para o usuário logado.
    """
    # Se o usuário não estiver logado, retorna um conjunto vazio.
    if not request.user.is_authenticated:
        return {'modulos_visiveis': set()}

    # Para superusuários, garante que eles vejam todos os módulos ativos.
    if request.user.is_superuser:
        modulos_permitidos = Modulo.objects.filter(ativo=True)
        slugs_permitidos = set(modulos_permitidos.values_list('slug', flat=True))
        return {'modulos_visiveis': slugs_permitidos}

    # Para usuários comuns, verifica os grupos.
    slugs_permitidos = set()
    try:
        grupos_do_usuario = request.user.groups.all()
        if grupos_do_usuario.exists():
            modulos_permitidos = Modulo.objects.filter(
                ativo=True,
                grupos_permitidos__in=grupos_do_usuario
            ).distinct()
            slugs_permitidos = set(modulos_permitidos.values_list('slug', flat=True))
    except Exception:
        # Se qualquer erro inesperado ocorrer, retorna um conjunto vazio por segurança.
        pass
        
    return {'modulos_visiveis': slugs_permitidos}


def logo_processor(request):
    """
    Disponibiliza a URL do logo ativo para todos os templates.
    """
    logo_url = None
    try:
        logo_config = LogoConfig.objects.filter(ativo=True).first()
        if logo_config and logo_config.logo:
            logo_url = logo_config.logo.url
    except Exception:
        # Em caso de erro (ex: tabela não existe durante o migrate), não faz nada.
        pass
        
    return {'logo_url_global': logo_url}


def tema_processor(request):
    """
    Disponibiliza o tema ativo para todos os templates.
    """
    tema_ativo = None
    try:
        tema_ativo = Tema.objects.filter(ativo=True).first()
        if not tema_ativo:
            # Se nenhum tema estiver marcado como ativo, ou se a tabela estiver vazia,
            # cria ou pega o primeiro que encontrar.
            tema_ativo = Tema.objects.first()
            if not tema_ativo:
                # Caso extremo: a tabela está completamente vazia. Cria um tema padrão.
                tema_ativo = Tema.objects.create(nome="Tema Padrão", ativo=True)
    except Exception:
        # Em caso de erro (ex: tabela não existe durante o migrate), não faz nada.
        pass
        
    return {'tema_ativo': tema_ativo}