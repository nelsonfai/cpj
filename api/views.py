# couples_diary_backend/api/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .serializers import CustomUserSerializer,UserInfoSerializer,CollaborativeListSerializer,ItemSerializer,CustomAuthTokenSerializer
from rest_framework.authtoken.views import ObtainAuthToken,APIView
from rest_framework.permissions import IsAuthenticated
from .models import CollaborativeList,Item
from .permissions import IsOwnerOrTeamMember,IsCollaborativeListMember
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.urls import get_resolver
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .authentication import EmailBackend



@api_view(['GET'])
@permission_classes([AllowAny])
def list_endpoints(request):
    urlconf = get_resolver()
    url_list = []

    def extract_endpoints(urlpatterns, namespace=''):
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):  # Recursive for include() patterns
                extract_endpoints(pattern.url_patterns, namespace + pattern.namespace + ':')
            if hasattr(pattern, 'callback') and hasattr(pattern.callback, '__name__'):
                url_list.append(namespace + pattern.pattern._route)

    extract_endpoints(urlconf.url_patterns)

    return Response(url_list)


class SignUpView(generics.CreateAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Create a token for the user
        token, created = Token.objects.get_or_create(user=serializer.instance)
        headers = self.get_success_headers(serializer.data)
        return Response({'token': token.key}, status=status.HTTP_201_CREATED, headers=headers)

class LoginView(ObtainAuthToken):
    serializer_class = CustomAuthTokenSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = [EmailBackend]  # Use the custom authentication class

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.pk, 'email': user.email}, status=status.HTTP_200_OK)

class UserProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data, status=status.HTTP_200_OK)


class UserInfoView(generics.RetrieveAPIView):
    serializer_class = UserInfoSerializer
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Simply delete the user's token to log them out
        request.auth.delete()
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)
    
#Collaborative Lists
class CollaborativeListCreateView(generics.CreateAPIView):
    queryset = CollaborativeList.objects.all()
    serializer_class = CollaborativeListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CollaborativeListRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CollaborativeList.objects.all()
    serializer_class = CollaborativeListSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTeamMember]

class UserCollaborativeListsView(generics.ListAPIView):
    serializer_class = CollaborativeListSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrTeamMember]

    def get_queryset(self):
        user = self.request.user
        return CollaborativeList.objects.filter(
            Q(user=user) | Q(team__member1=user) | Q(team__member2=user)
        )

    
class ItemCreateView(generics.CreateAPIView):
    """
    API endpoint for creating a new Item.
    """
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsCollaborativeListMember]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ItemRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a specific Item.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsCollaborativeListMember]

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.delete()
        return Response(status=204)


class CollaborativeListItemsView(generics.ListAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTeamMember]

    def get_queryset(self):
        collaborative_list = get_object_or_404(
            CollaborativeList, pk=self.kwargs['pk']
        )
        return Item.objects.filter(list=collaborative_list)


from django.db.models import Count, Sum

class UserCollaborativeListsView(generics.ListAPIView):
    serializer_class = CollaborativeListSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrTeamMember]

    def get_queryset(self):
        user = self.request.user
        queryset = CollaborativeList.objects.filter(
            Q(user=user) | Q(team__member1=user) | Q(team__member2=user)
        ).annotate(
            listitem_count=Count('item'),
            done_item_count=Sum('item__done')
        )

        return queryset
