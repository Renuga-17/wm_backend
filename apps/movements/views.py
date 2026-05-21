from rest_framework import viewsets
from .models import Movement
from .serializers import MovementSerializer

class MovementViewSet(viewsets.ModelViewSet):
    queryset = Movement.objects.all()
    serializer_class = MovementSerializer
