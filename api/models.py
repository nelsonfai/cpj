# couples_diary_backend/api/models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone

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
    fullname = models.CharField(max_length=100, blank=True,null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    lang = models.CharField(max_length=10,blank=True,null=True)
    team_invite_code = models.CharField(max_length=6, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    premium = models.BooleanField(default=True)
    expo_token = models.TextField(null=True,blank=True)
    notifications = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    def __str__(self):
        return self.email
    @property
    def is_premium (self):
        if self.premium:
            return True
        team = Team.objects.filter(Q(member1=self) | Q(member2=self)).first()
        if team and (team.member1.premium or team.member2.premium):
            return True
        return False
    
class Team(models.Model):
    unique_id = models.CharField(max_length=8, unique=True)
    member1 = models.OneToOneField(CustomUser, related_name='team_member1', on_delete=models.CASCADE,)
    member2 = models.OneToOneField(CustomUser, related_name='team_member2', on_delete=models.CASCADE, null=True, blank=True, )
    ismember1sync = models.BooleanField(default=False)
    ismember2sync = models.BooleanField(default=False)

    def __str__(self):
        return f"Team {self.unique_id} "

class CollaborativeList(models.Model):
    team = models.ForeignKey('Team',on_delete=models.SET_NULL,null=True,blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE ,null=True,blank=True )
    title = models.CharField(max_length=255)
    color = models.CharField(max_length=40,)
    description = models.TextField( null=True,blank=True)
    dateline= models.DateField(null=True,blank=True)
    def check_all_item_done(self):
        return not self.item_set.filter(done=False).exists()
    def check_past_dateline(self):
        undone =self.item_set.filter(done=False).exists()
        if self.dateline and undone:
            today = timezone.now().date()
            if today > self.dateline:
                return True

        return False
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
    habitidentifier = models.CharField(max_length=100 ,null=True,blank=True)
    icon =models.CharField(max_length=30,blank=True,null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    color= models.CharField(max_length=255,blank=True,null=True)
    name = models.CharField(max_length=255)
    frequency = models.CharField(max_length=50)
    description = models.TextField(blank=True,null=True)
    start_date = models.DateField()
    end_date = models.DateField( blank=True,null=True)
    reminder_time = models.DateTimeField(null=True, blank=True)
    specific_days_of_week = models.CharField(max_length=255, null=True, blank=True)
    specific_day_of_month = models.CharField(max_length=255, null=True, blank=True)  # Updated field

    def get_specific_days_as_list(self):
        if self.specific_days_of_week:
            return self.specific_days_of_week.split(',')
        return []
    def get_specific_month_days_as_list(self):
        if self.specific_days_of_week:
            return self.specific_day_of_month.split(',')
        return []

    def set_specific_days_from_list(self, days_list):
        self.specific_days_of_week = ','.join(days_list)

    def calculate_streak(self, user_id, current_date):
        progress_instances = DailyProgress.objects.filter(
            habit=self, user_id=user_id, progress=True, date__lte=current_date
        ).order_by('-date')

        streak = 0
        has_instance_with_current_date = any(instance.date == current_date for instance in progress_instances)
        if has_instance_with_current_date:
            previous_date = current_date
        else:
            previous_date = self.set_previous_day(date=current_date)

        for progress_instance in progress_instances:
            if progress_instance.date == previous_date:
                streak += 1
                previous_date = self.set_previous_day(date=previous_date)
            else:
                break
        return streak

    def set_previous_day(self, date):
        if self.frequency == 'daily':
            previous_date = date - timedelta(days=1)
        elif self.frequency == 'weekly':
            selected_days = self.get_specific_days_as_list()
            previous_date = date - timedelta(days=1)
            while True:
                current_day_of_week = previous_date.strftime('%A')
                if current_day_of_week in selected_days:
                    return previous_date
                previous_date -= timedelta(days=1)
        elif self.frequency == 'monthly':
            previous_date = date.replace(day=self.specific_day_of_month) - timedelta(days=1)
        return previous_date
    def __str__(self):
        return self.name

class DailyProgress(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    progress = models.BooleanField(default=False)  
    def __str__(self):
        return f"{self.user.email}'s progress for {self.habit.name} on {self.date}"
    

class Subscription(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    plan = models.CharField(max_length=255)
    stripe_customer_id = models.CharField(max_length=255)


class Notes (models.Model):
    team = models.ForeignKey('Team',on_delete=models.SET_NULL,null=True,blank=True)
    color = models.CharField(max_length=255,null=True,blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    body = models.TextField(null=True,blank=True)
    date = models.DateTimeField(auto_now=True)
    tags =models.CharField(max_length=255,null=True,blank=True)

    def save(self, *args, **kwargs):
        self.date = timezone.now()
        super(Notes, self).save(*args, **kwargs)
