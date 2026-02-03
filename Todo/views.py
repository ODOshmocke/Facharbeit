from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Todos
from .serializers import TodoSerializer
from django.shortcuts import render


def homePage(request):
    return render(request, 'home.html')


def addTodoPage(request):
    return render(request, 'add_todo.html')


def viewTodosPage(request):
    return render(request, 'todos.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def todos(request):
    items = Todos.objects.filter(user=request.user)
    serializer = TodoSerializer(items, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addTodo(request):
    serializer = TodoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        print("Todo Added Successfully")
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteTodo(request, pk):
    try:
        # Sicherstellen, dass der User nur sein eigenes Todo löscht
        todo = Todos.objects.get(pk=pk, user=request.user)
    except Todos.DoesNotExist:
        return Response({"error": "Nicht gefunden"}, status=status.HTTP_404_NOT_FOUND)

    todo.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateTodo(request, pk):
    try:
        todo = Todos.objects.get(pk=pk, user=request.user)
    except Todos.DoesNotExist:
        return Response({"error": "Nicht gefunden"}, status=status.HTTP_404_NOT_FOUND)

    # partial=True erlaubt es, nur einzelne Felder (z.B. nur 'completed') zu senden
    serializer = TodoSerializer(todo, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
