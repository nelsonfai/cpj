# couples_diary_backend/api/models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin
from datetime import timedelta

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30, blank=True,null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    team_invite_code = models.CharField(max_length=6, unique=True, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email
class Team(models.Model):
    unique_id = models.CharField(max_length=8, unique=True)
    member1 = models.OneToOneField(CustomUser, related_name='team_member1', on_delete=models.CASCADE,)
    member2 = models.OneToOneField(CustomUser, related_name='team_member2', on_delete=models.CASCADE, null=True, blank=True, )
    is_premium = models.BooleanField(default=False)

    def __str__(self):
        return f"Team {self.unique_id} "

class CollaborativeList(models.Model):
    team = models.ForeignKey('Team',on_delete=models.CASCADE,null=True,blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE ,null=True,blank=True )
    title = models.CharField(max_length=255)
    color = models.CharField(max_length=40,)
    description = models.TextField( null=True,blank=True)

    def __str__(self):
        return f"List '{self.title}'"

class Item(models.Model):
    list = models.ForeignKey(CollaborativeList, on_delete=models.CASCADE)
    text = models.TextField()
    done = models.BooleanField(default=False)

    def __str__(self):
        return self.text


# Daily Habit  Tracker 
class Habit(models.Model):

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    color= models.CharField(max_length=255,blank=True,null=True)
    name = models.CharField(max_length=255)
    frequency = models.CharField(max_length=50)
    description = models.TextField(blank=True,null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    reminder_time = models.TimeField(null=True, blank=True)
    specific_days_of_week = models.CharField(max_length=255, null=True, blank=True)

    def get_specific_days_as_list(self):
        if self.specific_days_of_week:
            return self.specific_days_of_week.split(',')
        return []

    def set_specific_days_from_list(self, days_list):
        self.specific_days_of_week = ','.join(days_list)

    def calculate_streak(self, user_id, current_date):
        progress_instances = DailyProgress.objects.filter(
            habit=self, user_id=user_id, progress=True, date__lte=current_date
        ).order_by('-date')

        streak = 0
        previous_date = current_date

        for progress_instance in progress_instances:
            if self.is_valid_streak_day(previous_date, progress_instance.date):
                streak += 1
                previous_date = progress_instance.date - timedelta(days=1)
            else:
                break

        return streak

    def is_valid_streak_day(self, previous_date, current_date):
        if self.frequency == 'daily':
            return current_date == previous_date - timedelta(days=1)
        elif self.frequency == 'weekly':
            return (
                current_date == previous_date - timedelta(days=1)
                and current_date.strftime('%A') in self.get_specific_days_as_list()
            )
        return False

    def __str__(self):
        return self.name
    def __str__(self):
        return self.name

class DailyProgress(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    progress = models.BooleanField(default=False)  
    def __str__(self):
        return f"{self.user.email}'s progress for {self.habit.name} on {self.date}"