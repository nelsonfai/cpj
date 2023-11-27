# api/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from .models import CustomUser,UserProfile
import random
import string


@receiver(post_save, sender=CustomUser)
def create_auth_token(sender, instance, created=False, **kwargs):
    print('creating auth token')
    print(instance)
    if created:
        print('auth token create started')
        Token.objects.create(user=instance)
        print('auth token created')


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created=False, **kwargs):
    print('creating user Profile')
    if created:
        UserProfile.objects.create(user=instance, team_invite_code=generate_invite_code())
def generate_invite_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))