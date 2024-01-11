from django.contrib import admin
from .models import Team, CollaborativeList, Item, Habit,CustomUser,DailyProgress,Notes
from django.contrib.auth import get_user_model  # Add this import

admin.site.register(Team)
admin.site.register(CollaborativeList)
admin.site.register(Item)
admin.site.register(Habit)
admin.site.register(DailyProgress)
admin.site.register(Notes)
admin.site.register(CustomUser)



