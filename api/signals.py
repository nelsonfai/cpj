# api/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from .models import CustomUser,DailyProgress
import random
import string
#from onesignal_sdk.client import Client

'''
@receiver(post_save, sender=CustomUser)
def create_auth_token(sender, instance, created=False, **kwargs):
    print('creating auth token')
    print(instance)
    if created:
        print('auth token create started')
        Token.objects.create(user=instance)
        print('auth token created')
''' 
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created=False, **kwargs):
    if created:
        instance.team_invite_code=generate_invite_code()
        instance.save()
def generate_invite_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

""" 
@receiver(post_save, sender=DailyProgress)
def habit_completed_notification(sender, instance, created, **kwargs):
    if created:
        habit_team= instance.habit.team
        if habit_team:
            team_member = habit_team.member1 if habit_team.member2 == instance.user else habit_team.member2
            client = Client(user_auth_key='YOUR_USER_AUTH_KEY', app_auth_key='YOUR_APP_AUTH_KEY')
            notification_content = {
                    'en': 'Habit completed!',
                }
            if team_member.onesignal_player_id:
                    client.create_notification(
                        contents=notification_content,
                        include_player_ids=[team_member.onesignal_player_id],
                    )

"""