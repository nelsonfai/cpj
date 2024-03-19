# api/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from .models import CustomUser,DailyProgress,Habit
import random
import string
import requests 
import uuid

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
@receiver(post_save,sender= Habit)
def habitIdentifier (instance,created,**kwargs):
    if created:
        try:
            id= generate_invite_code(10)
            habit_identifier = f'{id}{instance.frequency}'
            instance.habitidentifier= habit_identifier
            instance.save()
        except:
            pass
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created=False, **kwargs):
    if created:
        generated_uuid = uuid.uuid4()
        customerid = str(generated_uuid.hex)[:12]
        instance.team_invite_code=generate_invite_code(6)
        instance.customerid = customerid
        instance.save()
def generate_invite_code(number):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=number))



@receiver(post_save, sender=DailyProgress)
def habit_completed_notification(sender, instance, created, **kwargs):
    if created:
        habit_team = instance.habit.team
        if habit_team  and instance.user.is_premium:
            if habit_team.member2 != instance.user:
                team_member = habit_team.member1
                other_member = habit_team.member2
            else:
                team_member = habit_team.member2
                other_member = habit_team.member1
            if other_member.expo_token:
                send_message(
                    expo_token=other_member.expo_token,
                    title='Habit Completed!',
                    body=f'Your partner, {team_member.name}, just completed the habit: {instance.habit.name}.'
                )

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


