from django.shortcuts import render, HttpResponse
from .models import Todos
from .forms import TodoForm
# Create your views here.

def home(request):
    return render(request, "home.html")
def todos(request):
    return render(request, "todos.html", {"todos": Todos.objects.all()})

def addTodo(request):
    if request.method == "POST":
        form = TodoForm(request.POST)
        if form.is_valid():
            form.save()
            print("Todo Added Successfully")

            return render(request, "todos.html", {"todos": Todos.objects.all()})
    else:
        form = TodoForm()
    return render(request, "add_todo.html", {"form": form})