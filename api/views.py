# couples_diary_backend/api/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .serializers import CustomUserSerializer,UserInfoSerializer,CollaborativeListSerializer,ItemSerializer,CollaborativeListSerializerExtended,TeamSerializer,HabitSerializer,DailyProgressSerializer
from rest_framework.authtoken.views import ObtainAuthToken,APIView
from rest_framework.permissions import IsAuthenticated
from .models import CollaborativeList,Item,CustomUser,Team,Habit,DailyProgress
from .permissions import IsOwnerOrTeamMember,IsItemOwnerOrTeamMember
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.urls import get_resolver
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .authentication import EmailBackend
from rest_framework.authtoken.serializers import AuthTokenSerializer
from django.contrib.auth import authenticate
from rest_framework.generics import ListAPIView
import random,string
from datetime import datetime 
import calendar
from rest_framework.exceptions import PermissionDenied
from datetime import timedelta

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
    
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, *args, **kwargs):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
class LoginView(generics.GenericAPIView):
    serializer_class = AuthTokenSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')

        if email and password:
            user = authenticate(request=request, email=email, password=password)

            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({'token': token.key, 'user_id': user.pk, 'email': user.email}, status=status.HTTP_200_OK)

        return Response({'detail': 'Unable to log in with provided credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
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
    
class ChangeEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        new_email = request.data.get('new_email')

        if CustomUser.objects.filter(email=new_email).exclude(id=user.id).exists():
            return Response({'error': 'Email is already in use by another user.'}, status=status.HTTP_400_BAD_REQUEST)

        user.email = new_email
        user.save()

        return Response({'message': 'Email changed successfully.'}, status=status.HTTP_200_OK)



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
    def check_object_permissions(self, request, obj):
        if self.request.method == 'DELETE':
            if obj.user == request.user:
                return True
            else:
                return Response(
                    {'error': 'You do not have permission to delete this object.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().check_object_permissions(request, obj)

class ItemCreateView(generics.CreateAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsItemOwnerOrTeamMember]


class ItemRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a specific Item.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsItemOwnerOrTeamMember]

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.delete()
        return Response(status=204)


class CollaborativeListItemsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTeamMember]
    def get(self, request, pk):
        collaborative_list = get_object_or_404(CollaborativeList, pk=pk)
        
        # Serialize collaborative list data
        list_serializer = CollaborativeListSerializer(collaborative_list)
        list_info = list_serializer.data

        # Serialize items data
        items_queryset = collaborative_list.item_set.all()
        items_serializer = ItemSerializer(items_queryset, many=True)
        items_data = items_serializer.data

        # Construct the expected data structure
        expected_data = {
            'list_info': list_info,
            'items': items_data,
        }

        return Response(expected_data)

from django.db.models import Count, Sum

class UserCollaborativeListsView(generics.ListAPIView):
    serializer_class = CollaborativeListSerializerExtended
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

class TeamInvitationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, invite_code):
        # Get the logged-in user
        current_user = self.request.user

        # Check if the user is already a member of any team
        user_in_team = Team.objects.filter(Q(member1=current_user) | Q(member2=current_user)).exists()
        if user_in_team:
            return Response({'error': 'User is already in a team.'}, status=status.HTTP_400_BAD_REQUEST)

        # Find the user with the invite code
        invited_user = get_object_or_404(CustomUser, team_invite_code=invite_code)

        # Check if the invited user is the same as the logged-in user
        if invited_user == current_user:
            return Response({'error': 'Cannot create a team with yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the invited user is already a member of any team
        invited_user_in_team = Team.objects.filter(Q(member1=invited_user) | Q(member2=invited_user)).exists()
        if invited_user_in_team:
            return Response({'error': 'Invited user is already in a team.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new team with the invited user as member 1 and the current user as member 2
        team = Team.objects.create(
            unique_id=self.generate_unique_team_id(),
            member1=invited_user,
            member2=current_user,
        )

        # Clear the invite code for the invited user
        invited_user.team_invite_code = None
        invited_user.save()

        # Serialize the users and team for the response
        invited_user_serializer = CustomUserSerializer(invited_user)
        current_user_serializer = CustomUserSerializer(current_user)
        team_serializer = TeamSerializer(team)

        response_data = {
            'invited_user': invited_user_serializer.data,
            'current_user': current_user_serializer.data,
            'team': team_serializer.data,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    def generate_unique_team_id(self):
        # You should implement a method to generate a unique team ID
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

class UnpairTeamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Assuming the logged-in user is attempting to unpair their team
        current_user = self.request.user

        # Check if the user is a member of any team
        team = get_object_or_404(Team, Q(member1=current_user) | Q(member2=current_user))

        # Clear the team members and delete the team
        team.member1 = None
        team.member2 = None
        team.delete()

        return Response({'message': 'Team unpaired successfully.'}, status=status.HTTP_200_OK)



### Daily Habit tacker views

class HabitCreateView(generics.CreateAPIView):
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DailyProgressCreateView(generics.CreateAPIView):
    serializer_class = DailyProgressSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Get all Habits for User and related data for the given day
class HabitListView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            target_date = request.data.get('target_date')

            # Ensure that the user making the request matches the requested user_id
            if request.user.id != int(user_id):
                return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

            user_habits = Habit.objects.filter(user_id=user_id)
            
            # Parse the target_date string to a datetime object
            formatted_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            day_of_week = formatted_date.strftime('%A')  # Get the day of the week

            habits_data = []
            for habit in user_habits:

                progress_instance = DailyProgress.objects.filter(
                    habit=habit, user_id=user_id, date=formatted_date
                ).first()

                # Check if the habit should be included based on frequency and selected days
                include_habit = (
                    habit.frequency == 'daily' or
                    (habit.frequency == 'weekly' and day_of_week in habit.get_specific_days_as_list())
                )

                team = habit.team
                partner_count = 1
                partner_done_count = 0
                if progress_instance:
                    partner_done_count = 1


                if include_habit and team:
                    # Check if there is a progress instance for member 1
                    partner_count = 2
                    member_1_progress = DailyProgress.objects.filter(
                        habit=habit, user_id=team.member1.id, date=formatted_date
                    ).first()

                    # Check if there is a progress instance for member 2
                    member_2_progress = DailyProgress.objects.filter(
                        habit=habit, user_id=team.member2.id, date=formatted_date
                    ).first()

                    # If either member has progress, set partner_done to True
                    if member_1_progress or member_2_progress:
                        partner_done_count = 1
                    if member_1_progress and member_2_progress:
                        partner_done_count = 2

                if team == None:
                    isSharedValue = False
                else:
                    isSharedValue = True

                if include_habit:
                    streak = habit.calculate_streak(user_id, formatted_date)
                    habit_data = {
                        'id':habit.pk,
                        'color':habit.color,
                        "name": habit.name,
                        "description": habit.description,
                        "done": progress_instance.progress if progress_instance else False,
                        "streak": streak,
                        'partner_done_count':partner_done_count,
                        'partner_count':partner_count,
                        'start_date':habit.start_date,
                        'end_date':habit.end_date,
                        'specific_days_of_week':habit.specific_days_of_week,
                        'frequency': habit.frequency,
                         'reminder_time': habit.reminder_time,
                         'isShared':isSharedValue
                    }

                    habits_data.append(habit_data)

            return Response(habits_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HabitUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, habit_id):
        habit = get_object_or_404(Habit, pk=habit_id)
        serializer = HabitSerializer(habit, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HabitDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, habit_id):
        habit = get_object_or_404(Habit, pk=habit_id)
        # Check if the user making the request is the owner of the habit
        if habit.user != request.user:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        habit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_habit_as_done(request, habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)

    # Get the date from the request (assuming it is in the format 'YYYY-MM-DD')
    date_str = request.data.get('date')
    
    if not date_str:
        return Response({'error': 'Date is required'}, status=400)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format'}, status=400)

    # Check if a DailyProgress instance already exists for the same habit, user, and date
    existing_daily_progress = DailyProgress.objects.filter(
        habit=habit,
        user=request.user,
        date=date
    ).first()

    if existing_daily_progress:
        # If an instance already exists, delete it
        existing_daily_progress.delete()
    else:
        # If no instance exists, create a new DailyProgress instance
        DailyProgress.objects.create(
            habit=habit,
            user=request.user,
            date=date,
            progress=True  # Set progress as done
        )

    return Response({'success': True})


class HabitStatisticsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, habit_id):
        rangetype = request.GET.get('rangetype', 'monthly')
        habit = get_object_or_404(Habit, id=habit_id, user=request.user)

        if not habit.team:
            # If the habit does not belong to a team, return statistics for the logged-in user only
            partner1 = self.calculate_statistics(habit, request.user, request.GET.get('start_date'), request.GET.get('end_date'), rangetype)
            partner2 = {}
        else:
            team = habit.team
            partner1 = self.calculate_statistics(habit, request.user, request.GET.get('start_date'), request.GET.get('end_date'), rangetype)
            # Identify the other member of the team as partner2
            partner2_user = team.member1 if team.member2.id == request.user.id else team.member2
            partner2 = self.calculate_statistics(habit, partner2_user, request.GET.get('start_date'), request.GET.get('end_date'), rangetype)

        habit_info = {
            'habit_id': habit.id,
            'rangetype':rangetype,
            'habit_name': habit.name,
            'habit_color': habit.color,
            'habit_start_date': habit.start_date,
            'habit_end_date': habit.end_date,
            'habit_frequency': habit.frequency,
        }
        return Response({'habit_info': habit_info, 'partner1': partner1, 'partner2': partner2}, status=status.HTTP_200_OK)

    def calculate_statistics(self, habit, user, start_date, end_date, rangetype):
        # Convert start_date and end_date to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        if user.profile_pic:
                profile_pic = user.profile_pic.url
        else:
                profile_pic = None
        # Initialize the result dictionary
        result = {
            'user_id': user.id,
            'user_name': user.name,
            'profile': profile_pic,
            'completed_days_list': [],
        }

        if rangetype == 'monthly':
            progress_instances = DailyProgress.objects.filter(
                habit=habit, user_id=user.id, progress=True, date__range=(start_date, end_date)
            ).order_by('date')
            total_completed_days = progress_instances.count()
            total_undone_days = self.calculate_total_undone_days(habit, user, start_date, end_date,total_completed_days)
            completed_days_list = progress_instances.values_list('date', flat=True)
            result.update({
                'total_completed_days': total_completed_days,
                'total_undone_days': total_undone_days,
                'completed_days_list': list(completed_days_list),
            })
        elif rangetype == 'yearly':
                current_year = start_date.year  # Use the year from the start date
                for current_month in range(1, 13):
                        # Ensure to only consider months within the specified year
                        if current_year == start_date.year and current_month < start_date.month:
                            continue
                        if current_year == end_date.year and current_month > end_date.month:
                            break

                        # Calculate the first and last day of the current month
                        first_day = datetime(current_year, current_month, 1)
                        last_day = datetime(current_year, current_month, calendar.monthrange(current_year, current_month)[1])

                        progress_instances = DailyProgress.objects.filter(
                            habit=habit, user_id=user.id, progress=True, date__range=(first_day, last_day)
                        ).order_by('date')

                        total_completed_days = progress_instances.count()
                        total_undone_days = self.calculate_total_undone_days(habit, user, first_day, last_day, total_completed_days)

                        result['completed_days_list'].append({
                            'year': current_year,
                            'month': current_month,
                            'total_completed_days': total_completed_days,
                            'total_undone_days': total_undone_days,
                        })

                    
        return result
     

    def calculate_total_undone_days(self, habit, user, start_date, end_date,total_completed_days):

        date_range = (start_date, end_date)
        total_days = 0
        if habit.frequency == 'daily':
            total_days = (date_range[1] - date_range[0]).days + 1
        if habit.frequency == 'weekly':
            selected_days = [day.lower() for day in habit.get_specific_days_as_list()]
            print('Selected list',selected_days)
            total_days = sum(1 for day in date_range if day.strftime('%A').lower() in selected_days)
            print('total_days',total_days)
        total_undone_days = total_days - total_completed_days
        print(total_undone_days)
        return total_undone_days
