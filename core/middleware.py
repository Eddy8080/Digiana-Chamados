from django.shortcuts import redirect

class ForcePasswordChangeMiddleware:
    _EXEMPT = ('/alterar-senha/', '/logout/', '/login/', '/admin/', '/static/')

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
