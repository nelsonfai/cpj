# couples_diary_backend/api/models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
import string
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin

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
        return f"Team {self.unique_id} with members: {self.member1.name}, {self.member2.name if self.member2 else 'None'}"

class CollaborativeList(models.Model):
    team = models.ForeignKey('Team',on_delete=models.CASCADE,null=True,blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE ,null=True,blank=True )
    title = models.CharField(max_length=255)
    color = models.CharField(max_length=40,)
    description = models.TextField()

    def __str__(self):
        return f"List '{self.title}'"

class Item(models.Model):
    list = models.ForeignKey(CollaborativeList, on_delete=models.CASCADE)
    text = models.TextField()
    done = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class DiaryEntry(models.Model):
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    content = models.TextField()
    date = models.DateField()
    def __str__(self):
        return f"Entry on {self.date} for Team {self.team.unique_id}"

class MoodTracker(models.Model):
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    mood = models.CharField(max_length=50)
    date = models.DateField()

    def __str__(self):
        return f"Mood: {self.mood} on {self.date} for CustomUser {self.user.username} in Team {self.team.unique_id}"

class BillingInfo(models.Model):
    team = models.OneToOneField(Team, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=16)
    expiration_date = models.DateField()
    # Add other billing information fields as needed

    def __str__(self):
        return f"Billing info for team {self.team.unique_id}"


