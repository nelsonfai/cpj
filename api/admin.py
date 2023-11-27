from django.contrib import admin
from .models import Team, CollaborativeList, Item, DiaryEntry, MoodTracker, BillingInfo, UserProfile
from django.contrib.auth import get_user_model  # Add this import

CustomUser = get_user_model()  # Use get_user_model to reference the custom user model

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('unique_id', 'member1', 'member2', 'is_premium')
    search_fields = ('unique_id', 'member1__username', 'member2__username')
    # Customize other options as needed

@admin.register(CollaborativeList)
class CollaborativeListAdmin(admin.ModelAdmin):
    list_display = ('team', 'title', 'color', 'description')
    list_filter = ('team',)
    search_fields = ('title', 'team__unique_id')
    # Customize other options as needed

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('list', 'text', 'done')
    list_filter = ('list',)
    # Customize other options as needed

@admin.register(DiaryEntry)
class DiaryEntryAdmin(admin.ModelAdmin):
    list_display = ('team', 'content', 'date')
    list_filter = ('team', 'date')
    search_fields = ('content', 'team__unique_id')
    # Customize other options as needed

@admin.register(MoodTracker)
class MoodTrackerAdmin(admin.ModelAdmin):
    list_display = ('team', 'user', 'mood', 'date')
    list_filter = ('team', 'user', 'date')
    search_fields = ('mood', 'user__username', 'team__unique_id')
    # Customize other options as needed

@admin.register(BillingInfo)
class BillingInfoAdmin(admin.ModelAdmin):
    list_display = ('team', 'card_number', 'expiration_date')
    search_fields = ('team__unique_id', 'card_number')
    # Customize other options as needed

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_pic', 'team_invite_code')
    search_fields = ('user__username', 'team_invite_code')
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'is_staff')

