
from django.urls import path
from .views import SignUpView, LoginView,UserProfileUpdateView,UserInfoView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),

    path('update-profile/', UserProfileUpdateView.as_view(), name='update-profile'),
    path('profile-info/', UserInfoView.as_view(), name='profile-info'),

]