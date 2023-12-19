# couples_diary_backend/api/serializers.py
from rest_framework import serializers
from .models import CustomUser,CollaborativeList,Item,Team,Habit,DailyProgress
from rest_framework.authtoken.serializers import AuthTokenSerializer

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'profile_pic', 'password','lang')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user

class UserInfoSerializer(serializers.ModelSerializer):
    hasTeam = serializers.SerializerMethodField()
    team_id = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'profile_pic', 'team_invite_code', 'hasTeam', 'team_id','lang','premium')

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
        fields = ['id', 'team', 'user', 'title', 'color', 'description']

class CollaborativeListSerializerExtended(serializers.ModelSerializer):
    listitem_count = serializers.IntegerField()
    done_item_count = serializers.IntegerField()
    user_name = serializers.SerializerMethodField()
    has_team = serializers.SerializerMethodField()
    member1_name = serializers.SerializerMethodField()
    member2_name = serializers.SerializerMethodField()

    class Meta:
        model = CollaborativeList
        fields = ['id', 'team', 'user', 'user_name', 'member1_name', 'member2_name', 'title', 'color', 'description', 'listitem_count', 'done_item_count', 'has_team']

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