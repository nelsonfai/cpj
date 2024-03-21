# couples_diary_backend/api/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .serializers import CustomUserSerializer,UserInfoSerializer,CollaborativeListSerializer,ItemSerializer,CollaborativeListSerializerExtended,TeamSerializer,HabitSerializer,DailyProgressSerializer
from rest_framework.authtoken.views import ObtainAuthToken,APIView
from rest_framework.permissions import IsAuthenticated
from .models import CollaborativeList,Item,CustomUser,Team,Habit,DailyProgress,Notes,Subscription
from .permissions import IsOwnerOrTeamMember,IsItemOwnerOrTeamMember
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.urls import get_resolver
from django.db.models import Q, Count, Case, When, BooleanField
from django.shortcuts import get_object_or_404
from .authentication import EmailBackend
from rest_framework.authtoken.serializers import AuthTokenSerializer
from django.contrib.auth import authenticate
import random,string
from datetime import datetime ,timedelta
import calendar
from rest_framework.exceptions import PermissionDenied,ValidationError
from django.db import models
from .serializers import NotesSerializer
from django.utils import timezone
from django.conf import settings
import json
from django.http import JsonResponse
from .forms import CustomPasswordResetForm
from django.contrib.auth.views import PasswordResetConfirmView
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from mailjet_rest import Client
import os
from decouple import config



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
        expo_token = request.data.get('expo_token')


        if email and password:
            user = authenticate(request=request, email=email, password=password)
            if user:
                token, created = Token.objects.get_or_create(user=user)
                user.expo_token = expo_token
                user.save()
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
        user = request.user
        user.expo_token = None
        user.save()

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
                raise PermissionDenied(detail='You do not have permission to delete this object.', code='notCreatedUser')

        return super().check_object_permissions(request, obj)

class ItemCreateView(generics.CreateAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsItemOwnerOrTeamMember]


class ItemRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
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

from django.db.models import Count, Sum, Case, When, BooleanField

class UserCollaborativeListsView(generics.ListAPIView):
    serializer_class = CollaborativeListSerializerExtended
    permission_classes = [IsAuthenticated, IsOwnerOrTeamMember]

    def get_queryset(self):
        user = self.request.user
        queryset = CollaborativeList.objects.filter(
            Q(user=user) | Q(team__member1=user) | Q(team__member2=user)
        ).annotate(
            listitem_count=Count('item'),
            done_item_count=Sum(Case(When(item__done=True, then=1), default=0, output_field=BooleanField()))
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

class HabitCreateView(generics.CreateAPIView):
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.is_premium:
            serializer.save(user=user)
        else:
            habit_count = Habit.objects.filter(user=user).count()
            max_habit_limit = 3 
            if habit_count >= max_habit_limit:
                error_message = 'You have reached your habit limit.'
                raise ValidationError(error_message)
            else:
                teams = Team.objects.filter(Q(member1=user) | Q(member2=user))
                if teams:
                    team = teams.first()
                    if team.member1 == user:
                        team.ismember2sync = False
                    else:
                        team.ismember1sync = False
                    team.save()
                serializer.save(user=user)
                
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            return response
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
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
            user = request.user
            target_date = request.data.get('target_date')
            # Ensure that the user making the request matches the requested user_id
            if request.user.id != int(user_id):
                return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

            user_habits = Habit.objects.filter(Q(user=user) | Q(team__member1=user) | Q(team__member2=user))
            formatted_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            day_of_week = formatted_date.strftime('%A')  # Get the day of the week
            day_of_month = formatted_date.day
            if user_habits.count() >= 3 and not request.user.is_premium:
                limitreached = True
            else:
                limitreached = False

            # Parse the target_date string to a datetime object
            habits_data = []
            for habit in user_habits:

                progress_instance = DailyProgress.objects.filter(
                    habit=habit, user_id=user_id, date=formatted_date
                ).first()
                # Check if the habit should be included based on frequency and selected days
                specific_month_days = [int(day) for day in habit.get_specific_day_of_month_as_list()]
                include_habit = (
                    habit.frequency == 'daily' or
                    (habit.frequency == 'weekly' and day_of_week in habit.get_specific_days_as_list()) or
                    (habit.frequency == 'monthly' and int(day_of_month) in specific_month_days)
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
                    
                    streak = habit.calculate_streak(request.user.id, formatted_date)
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
                        'specific_day_of_month': habit.specific_day_of_month,
                        'frequency': habit.frequency,
                         'reminder_time': habit.reminder_time,
                         'isShared':isSharedValue,
                         'icon':habit.icon
                    }

                    habits_data.append(habit_data)
            return Response({'habits':habits_data,'limit':limitreached}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class HabitUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, habit_id):
        habit = get_object_or_404(Habit, pk=habit_id)
        serializer = HabitSerializer(habit, data=request.data)
        
        if serializer.is_valid():
            # Check if frequency, reminder_time, or specific_days_of_week has changed
            if (
                habit.frequency != serializer.validated_data.get('frequency') or
                habit.reminder_time != serializer.validated_data.get('reminder_time') or
                habit.specific_days_of_week != serializer.validated_data.get('specific_days_of_week')
            ):
                # Check if the habit has a team
                if habit.team:
                    # Check if the logged user is member1 or member2 of the team
                    if habit.team.member1 == request.user:
                        habit.team.ismember2sync = False
                        habit.team.save()
                    elif habit.team.member2 == request.user:
                        habit.team.ismember1sync = False
                        habit.team.save()
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
        if habit.team and habit.reminder_time:
            # Check if the user is member1 or member2 of the team
            if habit.team.member1 == request.user:
                habit.team.ismember2sync = False
                habit.team.save()
            elif habit.team.member2 == request.user:
                habit.team.ismember1sync = False
                habit.team.save()
        habit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_habit_as_done(request, habit_id):
    habit = get_object_or_404(Habit, Q(id=habit_id, user=request.user) | Q(id=habit_id, team__member1=request.user) | Q(id=habit_id, team__member2=request.user))
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
            'habit_icon':habit.icon
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
            total_days = self.calculate_total_days(habit, user, start_date, end_date)
            completed_days_list = progress_instances.values_list('date', flat=True)
            current_date = datetime.now().date()  # Get the current date
            current_streak = habit.calculate_streak(user.id, current_date)
            result.update({
                'total_completed_days': total_completed_days,
                'total_days': total_days,
                'completed_days_list': list(completed_days_list),
                'current_streak':current_streak
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
                        total_days = self.calculate_total_days(habit, user, first_day, last_day)

                        result['completed_days_list'].append({
                            'year': current_year,
                            'month': current_month,
                            'total_completed_days': total_completed_days,
                            'total_days': total_days,
                        })
        # Calculate streak for each partner
        current_date = datetime.now().date()  # Get the current date
        current_streak = habit.calculate_streak(user.id, current_date)

        result.update({
            'current_streak': current_streak,
        })   
        return result
    
    def calculate_total_days(self, habit, user, start_date, end_date):
        date_range = (start_date, end_date)
        total_days = 0
        if habit.frequency == 'daily':
            total_days = (date_range[1] - date_range[0]).days + 1
        if habit.frequency == 'weekly':
            selected_days = habit.get_specific_days_as_list()
            while start_date <= end_date:
                current_day = start_date.weekday()
                day_name = calendar.day_name[current_day]
                if day_name in selected_days:
                    total_days += 1
                start_date += timedelta(days=1)

        return total_days


class TeamHabitSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        current_date = datetime.now().date()
        team = Team.objects.filter(Q(member1=user) | Q(member2=user)).first()

        if not team:
            partner1_habits = self.calculate_summary(user, current_date)
            partner1_list = self.list_summary(user)
            partner1 = {
                "habits":partner1_habits,
                "list":partner1_list
            }
            partner2 = {
                
            }
        else:
            partner1_habits = self.calculate_summary(user, current_date)
            partner1_list = self.list_summary(user)

            partner2_user = team.member1 if team.member2.id == user.id else team.member2
            partner2_habits = self.calculate_summary(partner2_user, current_date)
            partner2_list = self.list_summary(partner2_user) 

            partner1 = {
                "habits":partner1_habits,
                "list":partner1_list
            }
            partner2 = {
                "habits":partner2_habits,
                "list":partner2_list
            }

        return Response({'partner1': partner1, 'partner2': partner2}, status=status.HTTP_200_OK)
    def list_summary(self, user):
        query = CollaborativeList.objects.filter(Q(user=user) | Q(team__member1=user) | Q(team__member2=user))
        total = query.count()
        num_past_dateline = 0
        num_completed = 0

        for collaborative_list in query:
            if collaborative_list.check_all_item_done():
                num_completed += 1

        for collaborative_list in query:
            if collaborative_list.check_past_dateline():
                num_past_dateline += 1

        return {
            'total': total,
            'num_past_dateline': num_past_dateline,
            'num_completed': num_completed
        }

    def calculate_summary(self, user, date):
        daily_habits = Habit.objects.filter(Q(user=user, frequency='daily') | Q(team__member1=user, frequency='daily') | Q(team__member2=user, frequency='daily'))
        weekly_habits = Habit.objects.filter(
            Q(user=user, frequency='weekly') | Q(team__member1=user, frequency='weekly') | Q(team__member2=user, frequency='weekly'),
            Q(specific_days_of_week__contains=date.strftime('%A'))  # Check if today is in the specific days list
        )
        all_habits = daily_habits | weekly_habits
        total_habits = all_habits.count()
        #total_habits = Habit.objects.filter(Q(user=user) | Q(team__member1=user) | Q(team__member2=user)).count()
        total_done = DailyProgress.objects.filter(user=user,date=date, progress=True).count()

        profile_pic = ''
        if user.profile_pic:
            profile_pic = user.profile_pic.url

        data = {
            'total_habits': total_habits,
            'total_done': total_done,
            'name': user.name,
            'profile': profile_pic
        }

        return data

class NotesListCreateView(generics.ListCreateAPIView):
        serializer_class = NotesSerializer
        permission_classes = [IsAuthenticated]
        
        def get_queryset(self):
            user = self.request.user
            queryset = Notes.objects.filter(
                Q(user=user) | Q(team__member1=user) | Q(team__member2=user)
            ).order_by('-date')
            return queryset

        def list(self, request, *args, **kwargs):
            queryset = self.get_queryset()
            user = self.request.user
            premium = user.is_premium
            num_notes = Notes.objects.filter(user=user).count()
            
            response_data = {
                'data': self.serializer_class(queryset, many=True).data,
                'limitreached': num_notes >= 3
            }
            
            return Response(response_data, status=status.HTTP_200_OK)

        def perform_create(self, serializer):
            user = self.request.user
            premium = user.is_premium  
            num_notes = Notes.objects.filter(user=user).count()
            
            if not premium and num_notes >= 3:
                error_message = 'You have reached your Note limit.'
                raise ValidationError(error_message)
            
            serializer.save(user=user, date=timezone.now())

class NotesDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Notes.objects.all()
    serializer_class = NotesSerializer
    permission_classes = [IsAuthenticated]
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

class NotesDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, note_id):
        note = get_object_or_404(Notes, pk=note_id)
        if note.user != request.user:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_habits(request):
    user = request.user
    user_habits = Habit.objects.filter(user=user)
    team_habits = Habit.objects.filter(
        Q(team__member1=user) | Q(team__member2=user)
    )
    teams = Team.objects.filter(Q(member1=user) | Q(member2=user))
    if teams:
        team = teams.first()
        if team.member1== user:
            team.ismember1sync = True
        else:
            team.ismember2sync =True
        team.save()
    all_habits = user_habits.union(team_habits)
    serializer = HabitSerializer(all_habits, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateUserFromWebhook(APIView):
    def post(self, request, *args, **kwargs):
        try:
            webhook_data = json.loads(request.body) # Assuming data is sent as JSON

            customid = webhook_data.get('customid')

            # Retrieve user data from webhook
            customid = webhook_data.get('customid')
            subscription_code = int(webhook_data.get('type'))  # Convert to int
            is_subscription_active = webhook_data.get('is_subscription_active')  
            productid = webhook_data.get('productid')
            auto_renew_status = webhook_data.get('auto_renew_status')
            event_date_ms = int(webhook_data.get('expire_date_ms'))  # Convert to int
            valid_till_date = datetime.utcfromtimestamp(event_date_ms / 1000)

            # Retrieve the user based on the customid
            user = CustomUser.objects.get(customerid=customid)
            
            # Gather all values before assigning
            premium = is_subscription_active
            subscription_type = "Yearly" if "yearly" in productid else "Monthly"
            store = webhook_data.get('store')
            valid_till = valid_till_date
            subscription_code = subscription_code
            productid = productid
            auto_renew_status = auto_renew_status

            # Update user based on the event code
            user.premium = premium
            user.valid_till = valid_till
            user.productid = productid
            user.auto_renew_status = auto_renew_status
            user.subscription_type = subscription_type
            user.store = store
            user.save()
            return Response({'message': 'User information updated successfully'}, status=200)
        
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        
        except Exception as e:
            print(f'Error:{e}')
            return Response({'error': str(e)}, status=500)



def request_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        print(f'Email received {email}-')
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        # Generate a password reset token
        token_generator = default_token_generator
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        # Construct the password reset link
        reset_url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})

        # Send the email with the password reset link
        #subject = 'Password Reset Request'
        #message = render_to_string('password_reset_email.html', {'reset_url': reset_url})
        sendPassReset(reset_link=reset_url,recipient_email=email)


        return JsonResponse({'message': 'Password reset email sent'})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomPasswordResetForm  # Your custom password reset form class
    template_name = 'password_reset_confirm.html'  # Your custom password reset confirmation template


def sendPassReset(reset_link,recipient_email):
    api_key = config('MJ_APIKEY_PUBLIC')
    api_secret = config('MJ_APIKEY_PRIVATE')
    #recipient_email = 'nelsonfai21@yahoo.com'
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    
    #reset_link = 'https://example.com/reset-password'  # Update with the actual reset link
    
    data = {
        'Messages': [
            {
                "From": {
                    "Email": 'contact@habts.us',
                    "Name": "Habts Us"  # Update with your name
                },
                "To": [
                    {
                        "Email": recipient_email,  # Update with recipient's email
                        "Name": recipient_email  # Update with recipient's name
                    }
                ],
                "Subject": "Password Reset Request",  # Update the subject
                "TextPart": "Click the link to reset your password.",  # Update the text part
                "HTMLPart": f"""
                    <div >
                        <p>Dear User,</p>
                        <p>We received a request to reset your password.</p>
                        <p>Please click the button below to reset your password:</p>
                        <p style="text-align: center;"><a href="{reset_link}" style="display: inline-block; padding: 10px 20px; background-color: #b0a7f7; color: #fff; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                        <p>If you did not request this, you can safely ignore this email.</p>
                        <p>Best regards,<br/>Habts Us Team</p>
                        <div style="width: 100%; text-align: center; background-color:#EFEDFD">
                            <div style="display: inline-block; width: 70px;">
                                <img src="https://habts.us/output-onlinegiftools.gif" alt="Animated GIF" style="max-width: 100%; height: auto; margin: 0 auto;">
                            </div>
                        </div>
                    </div>
                """
            }
        ]
    }

    try:
        return True  # Email sent successfully
    except Exception as e:
        return False  # Email sending failed