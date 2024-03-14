# authentication.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password):
            return user

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

class WebhookBearerAuthentication(BaseAuthentication):
    def authenticate(self, request):
        print('Got this ')
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            token_obj = Token.objects.get(key=token)
            return (token_obj.user, None)
        except Token.DoesNotExist:
            raise AuthenticationFailed('Invalid token')
