
from django.urls import path,include
from .views import SignUpView, LoginView,UserProfileUpdateView,UserInfoView,LogoutView,CollaborativeListCreateView,CollaborativeListRetrieveUpdateDestroyView,ItemCreateView,ItemRetrieveUpdateDestroyView,list_endpoints,UserCollaborativeListsView,CollaborativeListItemsView,TeamInvitationView,HabitCreateView,DailyProgressCreateView,HabitListView,mark_habit_as_done,HabitDeleteView,HabitUpdateView,HabitStatisticsView,UnpairTeamView,ChangeEmailView,ChangePasswordView,TeamHabitSummaryView,NotesListCreateView, NotesDetailView,NotesDeleteView,get_user_habits,UpdateUserFromWebhook,request_password_reset, password_reset_confirm,password_reset_complete,LeaderboardView,TeamStatsView,ArticleDetailView,ArticleListView,CalendarEventViewSet
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'events', CalendarEventViewSet, basename='event')

urlpatterns = [
    path('', include(router.urls)),

    path('list-endpoints/', list_endpoints, name='list-endpoints'),
    path('signup/', SignUpView.as_view(), name='signup'), #used
    path('login/', LoginView.as_view(), name='login'),#used
    path('logout/', LogoutView.as_view(), name='logout'),#used
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('change-email/', ChangeEmailView.as_view(), name='change-email'),


    path('request-password-reset/', request_password_reset, name='request_password_reset'),
    path('password/reset/complete/', password_reset_complete, name='password_reset_complete'),
    path('reset/<str:uidb64>/<str:token>/', password_reset_confirm, name='password_reset_confirm'),


    path('update-profile/', UserProfileUpdateView.as_view(), name='update-profile'),#used
    path('profile-info/', UserInfoView.as_view(), name='profile-info'),#used
    path('team-invitation/<str:invite_code>/', TeamInvitationView.as_view(), name='team-invitation'),
    path('unpair-team/', UnpairTeamView.as_view(), name='unpair-team'),
    path('team-stats/', TeamStatsView.as_view(), name='team-stats'),

    # Get all Collaborative lists in which iser is user or t.m1 or t.m2
    path('collaborative-lists/', UserCollaborativeListsView.as_view(), name='collaborative-list-create'),#used
    path('create-collabotive-list/', CollaborativeListCreateView.as_view(), name='create-collaborative-list'),
    # Endpoint for retrieving, updating, and deleting a specific CollaborativeList
    path('collaborative-lists/<int:pk>/', CollaborativeListRetrieveUpdateDestroyView.as_view(), name='collaborative-list-detail'),#used
    path('user-collaborative-lists/', UserCollaborativeListsView.as_view(), name='user-collaborative-lists'),
    path('collaborative-lists/<int:pk>/items/', CollaborativeListItemsView.as_view(), name='collaborative-list-items'),#used

    path('articles/', ArticleListView.as_view(), name='article-list'),
    path('articles/<slug:slug>/', ArticleDetailView.as_view(), name='article-detail'),

     # Endpoint for creating a new Item
    path('items/', ItemCreateView.as_view(), name='item-create'),
    # Endpoint for retrieving, updating, and deleting a specific Item
    path('items/<int:pk>/', ItemRetrieveUpdateDestroyView.as_view(), name='item-detail'), #used

    # ALL Habit Views
    path('habitsummary/', TeamHabitSummaryView.as_view(), name='habit-summary'),
    path('habits/create/', HabitCreateView.as_view(), name='habit-create'),
    path('daily-progress/create/', DailyProgressCreateView.as_view(), name='daily-progress-create'),
    path('habits/', HabitListView.as_view(), name='habit-list'),
    path('habits/<int:habit_id>/mark-as-done/', mark_habit_as_done, name='mark_habit_as_done'),
    path('habits/<int:habit_id>/update/', HabitUpdateView.as_view(), name='habit-update'),
    path('habits/<int:habit_id>/delete/', HabitDeleteView.as_view(), name='habit-delete'),
    path('habit/<int:habit_id>/statistics/', HabitStatisticsView.as_view(), name='habit_statistics'),
    path('notes/', NotesListCreateView.as_view(), name='notes-list-create'),
    path('notes/<int:pk>/', NotesDetailView.as_view(), name='notes-detail'),
    path('notes/<int:note_id>/delete/', NotesDeleteView.as_view(), name='note-delete'),
    path('sync_reminders/',get_user_habits, name='reminders'),
    path('update_user_from_webhook/', UpdateUserFromWebhook.as_view(), name='update_user_from_webhook'),
    #Game Mood
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
TeamHabitSummaryView
urlpatterns+=staticfiles_urlpatterns()
urlpatterns +=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)