from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .serializers import UserSerializer
from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@method_decorator(csrf_exempt, name='dispatch')
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)

    if user is not None:
        login(request, user)  # Hier wird die Session erstellt
        return Response({"detail": "Erfolgreich eingeloggt"})
    return Response({"detail": "Falsche Zugangsdaten"}, status=401)


@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({"detail": "Abgemeldet"})


@method_decorator(csrf_exempt, name='dispatch')
class SignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]  # Erlaubt jedem, sich zu registrieren
