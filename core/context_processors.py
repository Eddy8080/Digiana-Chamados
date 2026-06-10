from .models import PerfilUsuario

def role_context(request):
    if request.user.is_authenticated:
        return {'user_role': PerfilUsuario.role_for(request.user)}
    return {'user_role': ''}
