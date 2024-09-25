# middleware.py
from threading import local
from rest_framework.authtoken.models import Token

_user = local()

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated via DRF token
        user = request.user
        if not user.is_authenticated:
            token_key = request.headers.get('Authorization', '').split('Token ')[-1]
            if token_key:
                try:
                    token = Token.objects.get(key=token_key)
                    user = token.user
                except Token.DoesNotExist:
                    pass

        _user.value = user if user.is_authenticated else None
        response = self.get_response(request)
        return response

def get_current_user():
    return getattr(_user, 'value', None)
