
from django.urls import path
from .views import SignUpView, LoginView,UserProfileRetrieveView,UserProfileCreateView

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('create-profile/', UserProfileCreateView.as_view(), name='create-profile'),
    path('get-profile/', UserProfileRetrieveView.as_view(), name='get-profile'),
]
