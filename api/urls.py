
from django.urls import path
from .views import SignUpView, LoginView,UserProfileUpdateView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),

    path('update-profile/', UserProfileUpdateView.as_view(), name='update-profile'),

]
