
from django.urls import path
from .views import SignUpView, LoginView,UserProfileUpdateView,UserInfoView,LogoutView,CollaborativeListCreateView,CollaborativeListRetrieveUpdateDestroyView,ItemCreateView,ItemRetrieveUpdateDestroyView,list_endpoints,UserCollaborativeListsView,CollaborativeListItemsView

urlpatterns = [
    path('list-endpoints/', list_endpoints, name='list-endpoints'),

    path('signup/', SignUpView.as_view(), name='signup'), #used
    path('login/', LoginView.as_view(), name='login'),#used
    path('logout/', LogoutView.as_view(), name='logout'),#used

    path('update-profile/', UserProfileUpdateView.as_view(), name='update-profile'),#used
    path('profile-info/', UserInfoView.as_view(), name='profile-info'),#used

    # Get all Collaborative lists in which iser is user or t.m1 or t.m2
    path('collaborative-lists/', UserCollaborativeListsView.as_view(), name='collaborative-list-create'),#used
    # Endpoint for retrieving, updating, and deleting a specific CollaborativeList
    path('collaborative-lists/<int:pk>/', CollaborativeListRetrieveUpdateDestroyView.as_view(), name='collaborative-list-detail'),
    path('user-collaborative-lists/', UserCollaborativeListsView.as_view(), name='user-collaborative-lists'),
    path('collaborative-lists/<int:pk>/items/', CollaborativeListItemsView.as_view(), name='collaborative-list-items'),#used


     # Endpoint for creating a new Item
    path('items/', ItemCreateView.as_view(), name='item-create'),

    # Endpoint for retrieving, updating, and deleting a specific Item
    path('items/<int:pk>/', ItemRetrieveUpdateDestroyView.as_view(), name='item-detail'),

]
