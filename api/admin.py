from django.contrib import admin
from .models import Team, CollaborativeList, Item, DiaryEntry, MoodTracker, BillingInfo,CustomUser
from django.contrib.auth import get_user_model  # Add this import

admin.site.register(Team)
admin.site.register(CollaborativeList)
admin.site.register(Item)
admin.site.register(DiaryEntry)
admin.site.register(CustomUser)



