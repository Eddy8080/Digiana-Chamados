from django.shortcuts import redirect


class ForcePasswordChangeMiddleware:
    _EXEMPT = ('/alterar-senha/', '/logout/', '/login/', '/painel-adm/', '/static/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not any(request.path.startswith(p) for p in self._EXEMPT):
                try:
                    if request.user.perfil.must_change_password:
                        return redirect('alterar_senha')
                except Exception:
                    pass
        return self.get_response(request)


class SecurityHeadersMiddleware:
    """Adiciona CSP, Permissions-Policy e X-XSS-Protection em todas as respostas."""

    _CSP = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.tailwindcss.com cdn.ckeditor.com; "
        "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdn.ckeditor.com; "
        "font-src 'self' fonts.gstatic.com data:; "
        "img-src 'self' data: res.cloudinary.com; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('Content-Security-Policy', self._CSP)
        response.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.setdefault('X-XSS-Protection', '1; mode=block')
        return response
