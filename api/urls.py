
from django.urls import path
from .views import SignUpView, LoginView,UserProfileUpdateView,UserInfoView,LogoutView,CollaborativeListCreateView,CollaborativeListRetrieveUpdateDestroyView,ItemCreateView,ItemRetrieveUpdateDestroyView,list_endpoints

urlpatterns = [
    path('list-endpoints/', list_endpoints, name='list-endpoints'),

    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('update-profile/', UserProfileUpdateView.as_view(), name='update-profile'),
    path('profile-info/', UserInfoView.as_view(), name='profile-info'),

    # Endpoint for creating a new CollaborativeList
    path('collaborative-lists/', CollaborativeListCreateView.as_view(), name='collaborative-list-create'),
    # Endpoint for retrieving, updating, and deleting a specific CollaborativeList
    path('collaborative-lists/<int:pk>/', CollaborativeListRetrieveUpdateDestroyView.as_view(), name='collaborative-list-detail'),


     # Endpoint for creating a new Item
    path('items/', ItemCreateView.as_view(), name='item-create'),

    # Endpoint for retrieving, updating, and deleting a specific Item
    path('items/<int:pk>/', ItemRetrieveUpdateDestroyView.as_view(), name='item-detail'),

]
