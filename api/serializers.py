from rest_framework import serializers
from .models import CustomUser,CollaborativeList,Item,Team,Habit,DailyProgress,Notes,Gamification,Article,CalendarEvent,QuizScore
from rest_framework.authtoken.serializers import AuthTokenSerializer
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

class CustomUserSerializer(serializers.ModelSerializer):
    imageurl = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'profile_pic', 'password','lang','expo_token','imageurl','tourStatusSharedListDone','tourStatusNotesDone','tourStatusHabitsDone','joinNewsletter')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        lang = validated_data.get('lang', 'en') 
        print(validated_data)
        joinNewsletter = validated_data.get('joinNewsletter', False)
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            lang=lang,
            joinNewsletter= joinNewsletter
        )
        return user
    def get_imageurl(self, obj):
            if obj.profile_pic:
                return obj.profile_pic.url
        
class UserInfoSerializer(serializers.ModelSerializer):
    hasTeam = serializers.SerializerMethodField()
    team_id = serializers.SerializerMethodField()
    premium = serializers.SerializerMethodField()
    mypremium = serializers.SerializerMethodField()
    imageurl = serializers.SerializerMethodField()
    isync = serializers.SerializerMethodField()
    partner_name = serializers.SerializerMethodField() 
    partner_image = serializers.SerializerMethodField() 
    canReview = serializers.SerializerMethodField()
    changed_data = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'profile_pic', 'team_invite_code', 'hasTeam', 'team_id','lang','premium','isync','imageurl','customerid', 'subscription_type','valid_till', 'subscription_code', 'productid','mypremium','tourStatusSharedListDone','tourStatusNotesDone','tourStatusHabitsDone','partner_name','partner_image','canReview','changed_data')
    
    def get_hasTeam(self, user):
        return getattr(user, 'team_member1', None) is not None or getattr(user, 'team_member2', None) is not None
    def get_team_id(self, user):
        team_member1 = getattr(user, 'team_member1', None)
        team_member2 = getattr(user, 'team_member2', None)
        if team_member1:
            return user.team_member1.id
        elif team_member2:
            return user.team_member2.id
        return None
    
    def get_isync(self, user):
        if hasattr(user, 'team_member1') and user.team_member1:
            return user.team_member1.ismember1sync
        elif hasattr(user, 'team_member2') and user.team_member2:
            return user.team_member2.ismember2sync
        return False
    def get_imageurl(self,user):
        if user.profile_pic:
            return user.profile_pic.url
    def get_premium(self, user):
        return user.is_premium
    def get_mypremium(self, user):
        return user.premium
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['premium'] = instance.is_premium
        return representation
    
    def get_partner_name(self, user):
        team_member1 = getattr(user, 'team_member1', None)
        team_member2 = getattr(user, 'team_member2', None)
        if team_member1 and team_member1.member2:
            return team_member1.member2.name  # Partner is member2
        elif team_member2 and team_member2.member1:
            return team_member2.member1.name  # Partner is member1
        return None
    def get_partner_image(self, user):
        team_member1 = getattr(user, 'team_member1', None)
        team_member2 = getattr(user, 'team_member2', None)
        if team_member1 and team_member1.member2:
            if team_member1.member2.profile_pic:
                return team_member1.member2.profile_pic.url  # Partner is member2
        elif team_member2 and team_member2.member1:
            if team_member2.member1.profile_pic:
                return team_member2.member1.profile_pic.url  # Partner is member1
        return None
    def get_canReview(self, user):
        if user.hasReview:
            return False  
        # Check if the account was created more than 3 days ago
        account_age = timezone.now() - user.date_joined
        if account_age < timedelta(days=3):
            return False  # User's account is not old enough to leave a review

        return True
    
    def get_changed_data(self, user):
        team = Team.objects.filter(Q(member1=user) | Q(member2=user)).first()
        if team:
            if user == team.member1:
                return team.get_member1_changed_data()
            elif user == team.member2:
                return team.get_member2_changed_data()
        return []

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['premium'] = instance.is_premium
        return representation

"""class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'list', 'text', 'done']
    def create(self, validated_data):
        return Item.objects.create(**validated_data)
"""

class CollaborativeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollaborativeList
        fields = ['id', 'team', 'user', 'title', 'color', 'description','dateline']

class CollaborativeListSerializerExtended(serializers.ModelSerializer):
    listitem_count = serializers.IntegerField()
    done_item_count = serializers.IntegerField()
    user_name = serializers.SerializerMethodField()
    has_team = serializers.SerializerMethodField()
    member1_name = serializers.SerializerMethodField()
    member2_name = serializers.SerializerMethodField()

    class Meta:
        model = CollaborativeList
        fields = ['id', 'team', 'user', 'user_name', 'member1_name', 'member2_name', 'title', 'color', 'description', 'listitem_count', 'done_item_count', 'has_team','dateline']

    def get_user_name(self, obj):
        return obj.user.name if obj.user else None

    def get_has_team(self, obj):
        return obj.team is not None

    def get_member1_name(self, obj):
        return obj.team.member1.name if obj.team and obj.team.member1 else None

    def get_member2_name(self, obj):
        return obj.team.member2.name if obj.team and obj.team.member2 else None

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'list', 'text', 'done']


class CustomAuthTokenSerializer(AuthTokenSerializer):
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Modify the authentication data to use email instead of username
            attrs['username'] = email
            del attrs['email']
        return super().validate(attrs)

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'unique_id', 'member1', 'member2']
        read_only_fields = ['id', 'unique_id']

    validators = [
        serializers.UniqueTogetherValidator(
            queryset=Team.objects.all(),
            fields=['member1', 'member2'],
            message='Members must be unique in a team.'
        )
    ]

### Daily Habit Tracker Serializers
class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = '__all__'

class DailyProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyProgress
        fields = '__all__'
        
        
class NotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notes
        fields = ['id', 'team', 'user', 'title', 'body', 'date','color','tags']
        read_only_fields = ['user','date']


class UserSerializerPublic(serializers.ModelSerializer):
    imageurl = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'profile_pic', 'team_invite_code','imageurl']
    def get_imageurl(self, obj):
            if obj.profile_pic:
                return obj.profile_pic.url



class TeamLeaderboardSerializer(serializers.ModelSerializer):
    member1 = UserSerializerPublic()
    member2 = UserSerializerPublic(allow_null=True)  # Member 2 can be null
    total_points = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['unique_id', 'member1', 'member2', 'total_points']

    def get_total_points(self, obj):
        # Use the team_points method to get the combined points for the team
        return obj.team_points()

class GamificationSerializer(serializers.ModelSerializer):
    user = UserSerializerPublic()
    total_points = serializers.SerializerMethodField('get_total_points')
    partner_id = serializers.SerializerMethodField()
    logged_in_user_id = serializers.SerializerMethodField()
    logged_in_user_partner_id = serializers.SerializerMethodField()

    class Meta:
        model = Gamification
        fields = [
            'user', 'xp_points', 'habits_points', 'list_points', 'notes_points',
            'event_points', 'total_points', 'partner_id', 'logged_in_user_id', 'logged_in_user_partner_id'
        ]

    def get_total_points(self, obj):
        return obj.calculate_total_points()

    def get_partner_id(self, obj):
        # Fetch the partner's ID based on the user's team association
        team = Team.objects.filter(Q(member1=obj.user) | Q(member2=obj.user)).first()
        if team:
            if team.member1 == obj.user:
                return team.member2.id if team.member2 else None
            else:
                return team.member1.id if team.member1 else None
        return None

    def get_logged_in_user_id(self, obj):
        # Get the ID of the logged-in user from the request context
        request = self.context.get('request')
        return request.user.id if request else None

    def get_logged_in_user_partner_id(self, obj):
        # Get the partner's ID for the logged-in user based on their team association
        request = self.context.get('request')
        if request:
            logged_in_user = request.user
            team = Team.objects.filter(Q(member1=logged_in_user) | Q(member2=logged_in_user)).first()
            if team:
                if team.member1 == logged_in_user:
                    return team.member2.id if team.member2 else None
                else:
                    return team.member1.id if team.member1 else None
        return None



class ArticleSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()
    user_read = serializers.SerializerMethodField()  # New field for user read status
    partner_read = serializers.SerializerMethodField()  # New field for partner read status

    class Meta:
        model = Article
        fields = ['id', 'title', 'subtitle', 'author_name', 'image', 'image_url', 'slug', 'user_read', 'partner_read']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_title(self, obj):
        lang = self.context.get('language', 'en')
        return obj.title.get(lang, obj.title.get('en', ''))

    def get_subtitle(self, obj):
        lang = self.context.get('language', 'en')
        return obj.subtitle.get(lang, obj.subtitle.get('en', ''))

    def get_user_read(self, obj):
        user = self.context.get('user')
        if user.is_authenticated:
            return user in obj.read_by.all()
        return False

    def get_partner_read(self, obj):
        """
        Checks if the partner of the authenticated user has read the article.
        """
        user = self.context.get('user')
        if user.is_authenticated:
            # Check if the user is part of a team
            try:
                team = Team.objects.get(member1=user)  # Check if the user is member1
                partner = team.member2
            except Team.DoesNotExist:
                try:
                    team = Team.objects.get(member2=user)  # Check if the user is member2
                    partner = team.member1
                except Team.DoesNotExist:
                    partner = None  # User has no team/partner
                
            if partner:
                return partner in obj.read_by.all()
        return False
    def get_user_quiz_score(self, obj):
        """
        Returns the quiz score of the authenticated user for the current article.
        """
        user = self.context.get('user')
        if user.is_authenticated:
            try:
                # Fetch the quiz score for the user and the article
                quiz_score = QuizScore.objects.get(user=user, article=obj)
                return quiz_score.score
            except QuizScore.DoesNotExist:
                return None  # User has not taken the quiz yet
        return None

class ArticleDetailSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()
    body = serializers.SerializerMethodField()
    quiz = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    user_quiz_score = serializers.SerializerMethodField()  # New field for user quiz score

    class Meta:
        model = Article
        fields = ['id', 'title','created_date', 'subtitle', 'body', 'author_name', 'image', 'image_url', 'color', 'quiz','user_quiz_score']

    def get_language_specific_field(self, obj, field):
        lang = self.context.get('language', 'en')
        return getattr(obj, field).get(lang, getattr(obj, field).get('en', ''))

    def get_title(self, obj):
        return self.get_language_specific_field(obj, 'title')

    def get_subtitle(self, obj):
        return self.get_language_specific_field(obj, 'subtitle')

    def get_body(self, obj):
        return self.get_language_specific_field(obj, 'body')

    def get_quiz(self, obj):
        return self.get_language_specific_field(obj, 'quiz')

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
    def get_user_quiz_score(self, obj):
        """
        Returns the quiz score and selected answers of the authenticated user for the current article.
        """
        request = self.context.get('request')
        if request:
            user = request.user
            if user.is_authenticated:
                try:
                    # Fetch the quiz score for the user and the article
                    quiz_score = QuizScore.objects.get(user=user, article=obj)
                    return {
                        "score": quiz_score.score,
                        "selected_answers": quiz_score.selected_answers  # Return both score and selected answers
                    }
                except QuizScore.DoesNotExist:
                    return None  # User has not taken the quiz yet
        return None

class CalendarEventSerializer(serializers.ModelSerializer):
    is_shared = serializers.BooleanField(required=False)

    class Meta:
        model = CalendarEvent
        fields = ['id', 'summary', 'description', 'start_time', 'end_time', 'location', 'color', 'is_shared', 'user', 'team', 'type', 'event_source', 'recurrence', 'recurrence_type', 'recurrence_days', 'recurrence_day_of_month', 'reminders', 'status']
        read_only_fields = ['user', 'team']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['is_shared'] = instance.team is not None
        return ret

    def create(self, validated_data):
        is_shared = validated_data.pop('is_shared', False)
        user = self.context['request'].user
        team = None

        if is_shared:
            team = Team.objects.filter(Q(member1=user) | Q(member2=user)).first()

        event = CalendarEvent.objects.create(user=user, team=team, **validated_data)
        return event

    def update(self, instance, validated_data):
        is_shared = validated_data.pop('is_shared', instance.team is not None)
        user = self.context['request'].user

        if is_shared and not instance.team:
            team = Team.objects.filter(Q(member1=user) | Q(member2=user)).first()
            instance.team = team
        elif not is_shared:
            instance.team = None

        return super().update(instance, validated_data)