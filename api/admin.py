from django.contrib import admin
from .models import Team, CollaborativeList, Item, Habit,CustomUser,DailyProgress,Notes,Subscription,Gamification,Article,CalendarEvent,QuizScore
from django.contrib.auth import get_user_model  # Add this import

admin.site.register(Team)
admin.site.register(Subscription)

admin.site.register(CollaborativeList)
admin.site.register(CalendarEvent)
admin.site.register(Item)
admin.site.register(Habit)
admin.site.register(DailyProgress)
admin.site.register(Notes)
admin.site.register(CustomUser)
admin.site.register(Article)
admin.site.register(Gamification)
admin.site.register(QuizScore)
