from rest_framework import permissions
from .models import Team
from django.db.models import Q

class IsOwnerOrTeamMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or (obj.team and (request.user == obj.team.member1 or request.user == obj.team.member2))
    
class IsItemOwnerOrTeamMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if obj.list.team:
            return obj.list.user == request.user or (
            request.user == obj.list.team.member1 or request.user == obj.list.team.member2
        )
        else:
            return obj.list.user == request.user

class IsPremiumOrInPremiumTeam(permissions.BasePermission):
    message = "You must be a premium user or a member of a premium team to access this resource."

    def has_permission(self, request,):
        user = request.user
        if user.premium:
            return True
        team = Team.objects.filter(Q(member1=user) | Q(member2=user)).first()
        if team and (team.member1.premium or team.member2.premium):
            return True

        return False