# couples_diary_backend/api/views.py
from rest_framework import generics, permissions, status,viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from .serializers import CustomUserSerializer,UserInfoSerializer,CollaborativeListSerializer,ItemSerializer,CollaborativeListSerializerExtended,TeamSerializer,HabitSerializer,DailyProgressSerializer,GamificationSerializer,TeamLeaderboardSerializer,UserSerializerPublic,ArticleSerializer,ArticleDetailSerializer,CalendarEventSerializer,QuizScore
from rest_framework.authtoken.views import ObtainAuthToken,APIView
from rest_framework.permissions import IsAuthenticated
from .models import CollaborativeList,Item,CustomUser,Team,Habit,DailyProgress,Notes,Subscription,Gamification,Article,CalendarEvent
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
import os
from decouple import config
from django.shortcuts import render, redirect
from django.db import transaction

from django.contrib.auth.forms import SetPasswordForm
from .sendmail import sendPassReset
from .signals import send_message
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
        # Check if the 'is_shared' query parameter is set to True
        is_shared = self.request.data.get('isShared', False)
        # If shared, find the user's team
        team = None
        if is_shared:
            try:
                # Search for the team where the user is either member1 or member2
                team = Team.objects.filter(
                    models.Q(member1=self.request.user) | models.Q(member2=self.request.user)
                ).first()

                # If no team is found, raise an error
                if not team:
                    raise ValidationError("No team found for the current user.")
            except Team.DoesNotExist:
                raise ValidationError("No team exists for the current user.")

        # Save the CollaborativeList with the user and team (if found)
        serializer.save(user=self.request.user, team=team)

class CollaborativeListRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CollaborativeList.objects.all()
    serializer_class = CollaborativeListSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrTeamMember]
    def delete(self, request, *args, **kwargs):
        print('Delete called')
        obj = self.get_object()
        team = obj.team

        if obj.user == request.user:
            print('Deleted')
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if team and (team.member1 == request.user or team.member2 == request.user):
            print('Delete Team called')
            obj.team = None
            obj.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        raise PermissionDenied(detail='You do not have permission to delete this object.', code='notCreatedUser')

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
            unique_id=self.generate_unique_team_id(8),
            member1=invited_user,
            member2=current_user,
        )

        # Serialize the users and team for the response
        invited_user_serializer = UserSerializerPublic(invited_user)
        current_user_serializer = UserInfoSerializer(current_user)
        team_serializer = TeamSerializer(team)

        # Generate and assign new invite codes for both users
        new_invite_code_for_current_user = self.generate_unique_team_id(6)
        new_invite_code_for_invited_user = self.generate_unique_team_id(6)

        current_user.team_invite_code = new_invite_code_for_current_user
        invited_user.team_invite_code = new_invite_code_for_invited_user

        # Save the updated invite codes
        current_user.save()
        invited_user.save()
        # Access `.data` for serialized objects
        response_data = {
            'invited_user': invited_user_serializer.data,
            'current_user': current_user_serializer.data,
            'team': team_serializer.data,  # Add .data here
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    def generate_unique_team_id(self,legnth):
        # You should implement a method to generate a unique team ID
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=legnth))

class UnpairTeamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_user = self.request.user

        # Retrieve the team where the current user is a member
        team = get_object_or_404(Team, Q(member1=current_user) | Q(member2=current_user))

        try:
            with transaction.atomic():  # Begin transaction
                # Remove members and delete the team
                team.member1 = None
                team.member2 = None
                team.delete()

            # Transaction successful: Commit changes
            return Response({
                'message': 'Team unpaired successfully.',
                'hasTeam': False,
                'team_id': None
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # If any error occurs, transaction is rolled back
            return Response({
                'message': 'Error unpairing the team.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
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
                """
                teams = Team.objects.filter(Q(member1=user) | Q(member2=user))
                if teams:
                    team = teams.first()
                    if team.member1 == user:
                        team.ismember2sync = False
                    else:
                        team.ismember1sync = False
                    team.save()
                """
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
                        'icon':habit.icon,
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
        if habit.team and (request.user == habit.team.member1 or request.user == habit.team.member2) and habit.user != request.user:
            habit.team = None
            habit.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.user == habit.user:
            habit.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        else:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)



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
    def delete(self, request, pk):
        # Retrieve the note or return 404 if not found
        note = get_object_or_404(Notes, pk=pk)

        # Check if the user is a member of the team (member1 or member2) but not the owner of the note
        if note.team and (request.user == note.team.member1 or request.user == note.team.member2) and note.user != request.user:
            # If user is a team member but not the owner, nullify the team field instead of deleting the note
            note.team = None
            note.save()
            return Response({'detail': 'Team set to null instead of deleting the note.'}, status=status.HTTP_204_NO_CONTENT)

        # If the user is the owner of the note, allow deletion
        if request.user == note.user:
            note.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        # If neither condition is met, return a permission denied response
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
class NotesDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, note_id):
        # Retrieve the note or return 404 if not found
        note = get_object_or_404(Notes, pk=note_id)

        # Check if the user is a member of the team (member1 or member2) but not the owner of the note
        if note.team and (request.user == note.team.member1 or request.user == note.team.member2) and note.user != request.user:
            # If user is a team member but not the owner, nullify the team field instead of deleting the note
            note.team = None
            note.save()
            return Response({'detail': 'Team set to null instead of deleting the note.'}, status=status.HTTP_204_NO_CONTENT)

        # If the user is the owner of the note, allow deletion
        if request.user == note.user:
            note.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        # If neither condition is met, return a permission denied response
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_habits(request):
    user = request.user
    user_habits = Habit.objects.filter(user=user, reminder_time__isnull=False)
    
    # Filter team habits with reminder times
    team_habits = Habit.objects.filter(
        (Q(team__member1=user) | Q(team__member2=user)) & 
        Q(reminder_time__isnull=False)
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


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
        email = request.data.get('email')
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        # Generate a password reset token
        token_generator = default_token_generator
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        # Construct the password reset link
        g_url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        reset_url = f'https://auth.habts.us{g_url}'

        # Send the email with the password reset link
        #subject = 'Password Reset Request'
        #message = render_to_string('password_reset_email.html', {'reset_url': reset_url})
        #status = sendPassReset(reset_link=reset_url,recipient_email=email)
        status = sendPassReset(reset_link =reset_url, recipient_email=email, user_name=user.name, user_lang=user.lang)


        return JsonResponse({'message': 'Password reset email sent','status': status})
    



class LeaderboardView(generics.ListAPIView):
    serializer_class = GamificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get the "leaderboard_type" from query parameters ('user' or 'team')
        leaderboard_type = self.request.query_params.get('leaderboard_type', 'user')

        if leaderboard_type == 'user':
            # Return leaderboard for individual users
            return Gamification.leaderboard()
        elif leaderboard_type == 'team':
            # Return leaderboard for teams, ordered by total team points
            teams = Team.objects.all()  # You might want to filter based on active teams
            return sorted(teams, key=lambda team: team.team_points(), reverse=True)
        else:
            raise ValidationError("Invalid leaderboard_type. Must be 'user' or 'team'.")

    def get_serializer_class(self):
        leaderboard_type = self.request.query_params.get('leaderboard_type', 'user')
        if leaderboard_type == 'team':
            return TeamLeaderboardSerializer  # Use the team serializer for team leaderboard
        return GamificationSerializer  # Default to the user serializer

    def get_serializer_context(self):
        # Add the request to the context to access logged-in user and other details
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError,CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        # Token is valid, render the password reset form
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                return redirect('password_reset_complete')  # Redirect to a password reset complete page
        else:
            form = SetPasswordForm(user)
        return render(request, 'password_reset_confirm.html', {'form': form})
    else:
        return render(request, 'password_reset_invalid.html')

def password_reset_complete(request):
    return render(request, 'password_reset_complete.html')



from django.db.models import Q, Count, Max, F

from django.db.models import Q, Count, Max, F
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Team, Habit, CollaborativeList, Gamification, Item, Notes, DailyProgress

class TeamStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the current user
        current_user = request.user

        # Get the team where the current user is either member1 or member2
        team = Team.objects.filter(Q(member1=current_user) | Q(member2=current_user)).first()

        if not team:
            return Response({"error": "User is not a member of any team."}, status=400)

        # Determine the partner
        partner = team.member2 if team.member1 == current_user else team.member1

        # Include error handling and retrieve partner's name and image URL
        partner_info = {}
        if partner:
            partner_info = {
                'name':partner.name or None,  # Prioritizes fullname, then name, then email
                'imageurl': partner.profile_pic.url if partner.profile_pic else None  # Checks if profile_pic exists
            }
        else:
            partner_info = {"error": "No partner found."}
        # General Team Info
        current_date = timezone.now().date()
        team_duration_days = (current_date - team.created_at).days
        general_info = {
            'team_id': team.id,
            'unique_id': team.unique_id,
            'created_at': team.created_at,
            'team_duration_days': team_duration_days,
            'current_user': current_user.email,
            'partner_info': partner_info,
        }

        # Habits Summary for Team and Each User
        total_shared_habits = Habit.objects.filter(team=team).count()

        def get_user_habit_summary(user):
            try:
                habits = Habit.objects.filter(user=user, team=team)
                total_habits_created = habits.count()
                completed_habits = DailyProgress.objects.filter(user=user, habit__team=team, progress=True).count()
                habit_streak = 0  # Placeholder for streak calculation, if needed

                return {
                    'total_habits_created': total_habits_created,
                    'completed_habits': completed_habits,
                    'longest_streak': habit_streak,
                }
            except Exception as e:
                return {"error": f"Error fetching habit summary: {str(e)}"}

        habits_summary = {
            'total_shared_habits': total_shared_habits,
            'current_user': get_user_habit_summary(current_user),
            'partner': get_user_habit_summary(partner) if partner else None
        }

        # Gamification Summary (Only Points Related to Shared Activities)
        def get_gamification_summary(user):
            try:
                if hasattr(user, 'gamification'):
                    gamification = user.gamification
                    return {
                        'total_points': gamification.calculate_total_points(),
                        'xp_points': gamification.xp_points,
                        'habits_points': gamification.habits_points,
                        'list_points': gamification.list_points,
                        'notes_points': gamification.notes_points,
                        'event_points': gamification.event_points,
                        'formatted_points': gamification.formatted_points()
                    }
                return {}
            except Exception as e:
                return {"error": f"Error fetching gamification summary: {str(e)}"}

        gamemood_summary = {
            'current_user': get_gamification_summary(current_user),
            'partner': get_gamification_summary(partner) if partner else None,
            'team_position':  4  # Assuming a method exists to calculate this -- team.get_leaderboard_position()
        }

        # Notes Summary for Team and Each User
        total_shared_notes = Notes.objects.filter(team=team).count()

        def get_user_notes_summary(user):
            try:
                notes = Notes.objects.filter(user=user, team=team)
                total_notes_created = notes.count()
                recent_note_titles = list(notes.values_list('title', flat=True)[:5])

                return {
                    'total_notes_created': total_notes_created,
                    'recent_note_titles': recent_note_titles,
                }
            except Exception as e:
                return {"error": f"Error fetching notes summary: {str(e)}"}

        notes_summary = {
            'total_shared_notes': total_shared_notes,
            'current_user': get_user_notes_summary(current_user),
            'partner': get_user_notes_summary(partner) if partner else None
        }

        # Lists Summary for Team and Each User
        total_shared_lists = CollaborativeList.objects.filter(team=team).count()
        total_lists_past_deadline = Item.objects.filter(list__team=team, done=False, last_status_change__lt=timezone.now()).count()
        total_lists_completed = CollaborativeList.objects.filter(
            team=team
        ).annotate(
            total_items=Count('item'),
            completed_items=Count('item', filter=Q(item__done=True))
        ).filter(total_items=F('completed_items')).count()

        def get_user_lists_summary(user):
            try:
                lists = CollaborativeList.objects.filter(team=team, user=user)
                total_lists_created = lists.count()
                return {
                    'total_lists_created': total_lists_created
                }
            except Exception as e:
                return {"error": f"Error fetching lists summary: {str(e)}"}

        lists_summary = {
            'total_shared_lists': total_shared_lists,
            'total_lists_past_deadline': total_lists_past_deadline,
            'total_lists_completed': total_lists_completed,
            'current_user': get_user_lists_summary(current_user),
            'partner': get_user_lists_summary(partner) if partner else None
        }

        # Combine all summaries into a single response
        response_data = {
            'general_info': general_info,
            'habits_summary': habits_summary,
            'gamemood_summary': gamemood_summary,
            'notes_summary': notes_summary,
            'lists_summary': lists_summary,
        }

        return Response(response_data)


class ArticleListView(generics.ListAPIView):
    serializer_class = ArticleSerializer

    def get_queryset(self):
        return Article.objects.all().order_by('-created_date')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['language'] = self.request.query_params.get('lang', 'en')
        context['user'] = self.request.user if self.request.user.is_authenticated else None  # Add authenticated user to context
        return context


class ArticleDetailView(generics.RetrieveAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    lookup_field = 'slug'  # Retrieve based on the slug field

class ArticleDetailView(generics.RetrieveAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleDetailSerializer
    lookup_field = 'slug'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['language'] = self.request.query_params.get('lang', 'en')
        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        # Add user to the `read_by` field if authenticated
        article = self.get_object()
        user = request.user
        
        if user.is_authenticated:
            article.read_by.add(user)
        
        return response
    def post(self, request, *args, **kwargs):
            """
            Handle quiz score submission. Create or update the QuizScore entry.
            """
            article = self.get_object()
            user = request.user

            # Validate and deserialize the incoming data
            score = request.data.get('score')
            selected_answers = request.data.get('selected_answers')

            if score is None or selected_answers is None:
                return Response({"error": "Score and selected answers are required."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if a score already exists for this user and article
            quiz_score, created = QuizScore.objects.update_or_create(
                user=user,
                article=article,
                defaults={'score': score, 'selected_answers': selected_answers}
            )

            if created:
                return Response({"message": "Quiz score created successfully.", "score": quiz_score.score}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message": "Quiz score updated successfully.", "score": quiz_score.score}, status=status.HTTP_200_OK)

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from datetime import datetime

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from datetime import datetime
from .models import CalendarEvent, Team
from .serializers import CalendarEventSerializer


class CalendarEventViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        # If no start_date is provided, return no events for the list view
        if not start_date and not self.kwargs.get('pk'):
            return CalendarEvent.objects.none()

        # If accessing a specific event by ID (pk), don't apply date filters
        if self.kwargs.get('pk'):
            return CalendarEvent.objects.filter(
                Q(user=user) | Q(team__member1=user) | Q(team__member2=user)
            )

        # Apply date filters for the event list view
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        return CalendarEvent.objects.filter(
            (Q(user=user) | Q(team__member1=user) | Q(team__member2=user)) &
            (Q(start_time__date__range=(start_date, end_date)) | Q(end_time__date__range=(start_date, end_date)))
        ).order_by('start_time')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response({"detail": "You do not have permission to delete this event."},
                            status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
import time  # Use the synchronous sleep instead of asyncio.sleep
from rest_framework.authentication import TokenAuthentication,SessionAuthentication
import sys
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.models import AnonymousUser

class SSEStreamView(View):
    def get(self, request):
        user = self.get_authenticated_user(request)
        if user is None:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        def event_stream(user_id):
            last_data = None
            try:
                while True:
                    cache_key = f'user_info_{user_id}'
                    current_data = cache.get(cache_key)
                    if current_data != last_data:
                        yield f"data: {json.dumps(current_data)}\n\n"
                        last_data = current_data
                        
                        # Clear the changed data after sending
                        team = Team.objects.filter(Q(member1_id=user_id) | Q(member2_id=user_id)).first()
                        if team:
                            team.clear_changed_data(user)

                    time.sleep(1)
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        try:
            user_id = user.id
            response = StreamingHttpResponse(event_stream(user_id), content_type='text/event-stream')
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def get_authenticated_user(self, request):
        # Check for session-based authentication
        if request.user and request.user.is_authenticated:
            return request.user

        # Check for token-based authentication
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token_key = auth_header.split()[1]
                token = Token.objects.get(key=token_key)
                return token.user
            except (IndexError, Token.DoesNotExist):
                pass

        return None

    def handle_exception(self, exc):
        print(f"Unhandled exception in SSEStreamView: {str(exc)}", file=sys.stderr)
        return JsonResponse({'error': str(exc)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nudge_partner(request, habit_id):
    try:
        habit = Habit.objects.get(id=habit_id)
        if habit.team:
            team = habit.team
            current_user = request.user

            if current_user == team.member1:
                partner = team.member2
            elif current_user == team.member2:
                partner = team.member1
            else:
                partner = None

            if partner and partner.expo_token:
                title = f"Habit Reminder from {current_user.username}"
                body = f"Your partner is nudging you about the habit: {habit.name}"
                send_message(partner.expo_token, title, body)

    except Exception:
        # Silently handle any exceptions
        pass

    # Always return 200 OK
    return Response({"message": "Request processed"}, status=status.HTTP_200_OK)


class DeleteAccountView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        user = request.user  # Get the authenticated user

        # Check if the user belongs to a team and handle it accordingly
        team = Team.objects.filter(Q(member1=user) | Q(member2=user)).first()
        
        if team:
            team.delete()
        try:
            # Start transaction: delete user and related data
            user.delete()
            # Success response
            return Response(
                {"message": "Your account has been successfully deleted."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            # Rollback transaction in case of any error
            transaction.set_rollback(True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )