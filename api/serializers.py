# couples_diary_backend/api/serializers.py
from rest_framework import serializers
from .models import CustomUser,CollaborativeList,Item,Team,Habit,DailyProgress,Notes
from rest_framework.authtoken.serializers import AuthTokenSerializer

class CustomUserSerializer(serializers.ModelSerializer):
    imageurl = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'profile_pic', 'password','lang','expo_token','imageurl','tourStatusSharedListDone','tourStatusNotesDone','tourStatusHabitsDone')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            expo_token=validated_data['expo_token'],
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

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'profile_pic', 'team_invite_code', 'hasTeam', 'team_id','lang','premium','isync','imageurl','customerid', 'subscription_type','valid_till', 'subscription_code', 'productid','mypremium','tourStatusSharedListDone','tourStatusNotesDone','tourStatusHabitsDone')
    
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
        fields = ['id', 'unique_id', 'member1', 'member2', 'is_premium']
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