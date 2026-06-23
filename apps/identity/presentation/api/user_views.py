# pyrefly: ignore [missing-import]
from rest_framework import viewsets
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from common.permissions import ReadOnlyOrAuthenticated

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [ReadOnlyOrAuthenticated]

