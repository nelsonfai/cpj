from rest_framework import permissions

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

