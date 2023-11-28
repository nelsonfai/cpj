# couples_diary_backend/api/serializers.py
from rest_framework import serializers
from .models import CustomUser,CollaborativeList,Item

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'profile_pic', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'name', 'profile_pic','team_invite_code')


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'list', 'text', 'done']

    def create(self, validated_data):
        # Add the current user to the created Item
        user = self.context['request'].user
        return Item.objects.create(user=user, **validated_data)


class CollaborativeListSerializer(serializers.ModelSerializer):
    listitem_count = serializers.IntegerField()
    done_item_count = serializers.IntegerField()

    class Meta:
        model = CollaborativeList
        fields = ['id', 'team', 'user', 'title', 'color', 'description', 'listitem_count', 'done_item_count']



