# api/signals.py
from django.db.models.signals import post_save,pre_save,post_delete
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from .models import CustomUser,DailyProgress,Habit,CollaborativeList,Item,Gamification,Notes,CalendarEvent,Team
import random
import string
import requests 
import uuid
from django.utils.translation import gettext as _
from django.utils import translation
from django.utils import timezone
from datetime import timedelta,datetime
from .sendmail import sendWelcomeEmail
from .middleware import get_current_user
from .serializers import UserInfoSerializer
from django.core.cache import cache
#from onesignal_sdk.client import Client

def update_user_cache(user):
    serializer = UserInfoSerializer(user)
    cache.set(f'user_info_{user.id}', serializer.data, timeout=None)

@receiver(post_save, sender=Team)
def team_post_save(sender, instance, **kwargs):
    # Update cache for both members
    update_user_cache(instance.member1)
    if instance.member2:
        update_user_cache(instance.member2)

@receiver(post_save, sender=CustomUser)
def user_post_save(sender, instance, **kwargs):
    update_user_cache(instance)

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
color = '#c5bef9'

#@receiver (post_save,sender=CustomUser )
#def create_user_test_instances


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
        instance.team_invite_code = generate_invite_code(6)
        instance.customerid = customerid
        instance.save()
        
        # Set language preferences
        user_lang = instance.lang if instance.lang else 'en'

        # Translation mapping for languages (en, fr, de)
        translations = {
            'en': {
                'list_title': 'Our Shared Goals List',
                'list_description': 'A shared space to track tasks and goals together.',
                'item_text': 'Sample task: Plan our weekly activities',
                'habit_name': 'Daily Check-in with Partner',
                'habit_description': 'Take 10 minutes to connect and discuss the day.',
                'note_title': 'Weekly Reflections',
                'note_body': 'Write down reflections from this week to improve next week’s productivity and relationship.'
            },
            'fr': {
                'list_title': 'Notre Liste d\'Objectifs Partagés',
                'list_description': 'Un espace partagé pour suivre les tâches et les objectifs ensemble.',
                'item_text': 'Tâche d\'exemple : Planifier nos activités hebdomadaires',
                'habit_name': 'Vérification Quotidienne avec le Partenaire',
                'habit_description': 'Prenez 10 minutes pour vous connecter et discuter de la journée.',
                'note_title': 'Réflexions Hebdomadaires',
                'note_body': 'Écrivez vos réflexions de la semaine pour améliorer la productivité et la relation.'
            },
            'de': {
                'list_title': 'Unsere Gemeinsame Zielliste',
                'list_description': 'Ein gemeinsamer Raum, um Aufgaben und Ziele zusammen zu verfolgen.',
                'item_text': 'Beispielaufgabe: Planen Sie unsere wöchentlichen Aktivitäten',
                'habit_name': 'Täglicher Check-in mit dem Partner',
                'habit_description': 'Nehmen Sie sich 10 Minuten Zeit, um sich zu verbinden und den Tag zu besprechen.',
                'note_title': 'Wöchentliche Reflexionen',
                'note_body': 'Notieren Sie die Reflexionen dieser Woche, um die Produktivität und die Beziehung zu verbessern.'
            }
        }

        # Use the appropriate translation based on the user's language
        translated_texts = translations.get(user_lang, translations['en'])

        # Gamification element created for user
        Gamification.objects.create(user=instance)

        # Create Collaborative List Sample
        today_date = timezone.now()
        list = CollaborativeList.objects.create(
            user=instance,
            title=translated_texts['list_title'],
            color=color,  # Using the predefined color variable
            description=translated_texts['list_description'],
            dateline=today_date
        )
        Item.objects.create(list=list, text=translated_texts['item_text'])

        # Create Habit Sample
        Habit.objects.create(
            user=instance,
            frequency='daily',
            name=translated_texts['habit_name'],
            description=translated_texts['habit_description'],
            color=color,  # Using the predefined color variable
            start_date=today_date,
            icon='check-square-o'
        )

        # Create a Sample Note
        Notes.objects.create(
            user=instance,
            color=color,  # Using the predefined color variable
            title=translated_texts['note_title'],
            body=translated_texts['note_body']
        )
        sendWelcomeEmail(user_name = instance.name ,recipient_email=instance.email,user_lang=instance.lang)
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

########
def notify_partner(instance,title,bodyCode):
    list_team = instance.team
    if list_team:
        if list_team.member2 != instance.user:
            team_member = list_team.member1
            other_member = list_team.member2
        else:
            team_member = list_team.member2
            other_member = list_team.member1

        if other_member.expo_token:

            user_language = other_member.lang or 'en'  # Fallback to English if no language is set
            with translation.override(user_language):
                if bodyCode == 'list':
                    body = _(f'Your partner, {team_member.name}, just added a new Shared List: {instance.title}. Dive in and start checking things off together!')
                elif bodyCode == 'habit':
                    body = _(f'Your partner, {team_member.name}, just created a new Habit: {instance.name}. Stay on track and motivate each other every step of the way!')
                elif bodyCode == 'taskdone':
                    body = _(f'Your partner, {team_member.name}, just completed task on the Shared List: {instance.title}.Keep the momentum going!')
                else:
                    body = _(f'Your partner, {team_member.name}, just added a new Task to the Shared List: {instance.title}.Keep the momentum going and crush your goals together!')

            send_message(
                expo_token=other_member.expo_token,
                title=title,
                body=body
            )

@receiver(post_save, sender=CollaborativeList)
def partner_createslist_and_shares(instance, created, **kwargs):
    if created:
        notify_partner(instance=instance,title=instance.title,bodyCode='list')

@receiver(post_save, sender=Habit)
def partner_creates_habitslist(instance, created, **kwargs):
    if created:
        notify_partner(instance=instance,title=instance.name,bodyCode='habit')

@receiver(post_save, sender=Item)
def partner_creates_task(instance, created, **kwargs):
    if created:
        notify_partner(instance=instance.list,title="New task",bodyCode='task')

previous_done_states = {}

@receiver(pre_save, sender=Item)
def track_previous_done_state(sender, instance, **kwargs):
    if instance.id:  # Only check for existing objects
        previous_instance = sender.objects.get(pk=instance.id)
        previous_done_states[instance.id] = previous_instance.done  # Store the 'done' state

@receiver(post_save, sender=Item)
def partner_completes_task(instance, **kwargs):
    # Fetch the previous 'done' state from pre_save tracking
    previous_done = previous_done_states.get(instance.id)

    # Ensure previous state exists and check if task was just marked as done
    if previous_done is not None and not previous_done and instance.done:
        # Check if the last status change was more than 10 minutes ago
        if instance.last_status_change and timezone.now() - instance.last_status_change < timedelta(minutes=10):
            print("Task status was changed less than 10 minutes ago, skipping notification.")
            return  # Exit if it's less than 10 minutes since the last change

        notify_partner(instance=instance.list, title="Task Completed", bodyCode='taskdone')
        print('4')

    # Clean up the dictionary after use
    if instance.id in previous_done_states:
        del previous_done_states[instance.id]

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


# Data Synching 
def update_other_member_sync_status(team, user):
    if team and team.member1 and team.member2:
        if user == team.member1:
            team.ismember2sync = False
        elif user == team.member2:
            team.ismember1sync = False
        team.save()

# CollaborativeList signals
@receiver(post_save, sender=CollaborativeList)
def update_team_sync_on_list_change(sender, instance, created, **kwargs):
    user = instance.user if created else get_current_user()
    if instance.team and (created or instance.tracker.changed()):
        update_other_member_sync_status(instance.team, user)

@receiver(post_delete, sender=CollaborativeList)
def update_team_sync_on_list_delete(sender, instance, **kwargs):
    user = get_current_user()
    update_other_member_sync_status(instance.team, user)

# Item signals
@receiver(post_save, sender=Item)
def update_team_sync_on_item_change(sender, instance, created, **kwargs):
    user = instance.list.user if created else get_current_user()
    if created or instance.tracker.changed():
        update_other_member_sync_status(instance.list.team, user)

@receiver(post_delete, sender=Item)
def update_team_sync_on_item_delete(sender, instance, **kwargs):
    user = get_current_user()
    update_other_member_sync_status(instance.list.team, user)

# Habit signals
@receiver(post_save, sender=Habit)
def update_team_sync_on_habit_change(sender, instance, created, **kwargs):
    user = instance.user if created else get_current_user()
    if created or instance.tracker.changed():
        update_other_member_sync_status(instance.team, user)

@receiver(post_delete, sender=Habit)
def update_team_sync_on_habit_delete(sender, instance, **kwargs):
    user = get_current_user()
    update_other_member_sync_status(instance.team, user)

# DailyProgress signals (only create and delete)
@receiver(post_save, sender=DailyProgress)
def update_team_sync_on_progress_create(sender, instance, created, **kwargs):
    user = instance.user if created else get_current_user()
    today = timezone.now().date()

    # Check if the date of the instance matches today's date
    if created and instance.date == today:
        update_other_member_sync_status(instance.habit.team, user)

@receiver(post_delete, sender=DailyProgress)
def update_team_sync_on_progress_delete(sender, instance, **kwargs):
    user = get_current_user()
    update_other_member_sync_status(instance.habit.team, user)

# Notes signals
@receiver(post_save, sender=Notes)
def update_team_sync_on_notes_change(sender, instance, created, **kwargs):
    user = instance.user if created else get_current_user()
    if created or instance.tracker.changed():
        update_other_member_sync_status(instance.team, user)

@receiver(post_delete, sender=Notes)
def update_team_sync_on_notes_delete(sender, instance, **kwargs):
    user = get_current_user()
    update_other_member_sync_status(instance.team, user)

# CalendarEvent signals
@receiver(post_save, sender=CalendarEvent)
def update_team_sync_on_event_change(sender, instance, created, **kwargs):
    user = instance.user if created else get_current_user()
    if created or instance.tracker.changed():
        update_other_member_sync_status(instance.team, user)

@receiver(post_delete, sender=CalendarEvent)
def update_team_sync_on_event_delete(sender, instance, **kwargs):
    user = get_current_user()
    update_other_member_sync_status(instance.team, user)