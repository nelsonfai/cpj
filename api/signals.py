# api/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from .models import CustomUser,DailyProgress
import random
import string
import requests 

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

@receiver(post_save, sender=DailyProgress)
def habit_completed_notification(sender, instance, created, **kwargs):
    if created:
        habit_team = instance.habit.team
        if habit_team: # and instance.user.is_premium:
            team_member = habit_team.member1 if habit_team.member2 == instance.user else habit_team.member2

            if team_member.expo_token:
                send_message(expo_token=team_member.expo_token,title='Habit Done',body='Your Partner Just completed the Task')

def send_message(expo_token, title, body):
    expo_url = 'https://exp.host/--/api/v2/push/send'
    expo_data = {
        'to': expo_token,
        'title': title,
        'body': body,
    }

    try:
        response = requests.post(expo_url, json=expo_data)
        response_data = response.json()

        if response_data.get('status') == 'ok':
            print('Push notification sent successfully:', response_data)
        else:
            print('Failed to send push notification:', response_data)

    except Exception as e:
        print('Error sending push notification:', e)


