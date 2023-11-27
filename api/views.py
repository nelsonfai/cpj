# api/views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes, api_view

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def secure_view(request):
    # Your secure view logic here
    return Response({"message": "This is a secure view"})
