from django.urls import path
from . import views

urlpatterns = [
    path('/addTodo/', views.addTodo, ),
    # path('/getTodo/<int:pk>/', views.getTodo, ),
    path('/getTodos/', views.todos, ),

    # ein genaues item bekommen

    path('/deletetodo/<int:pk>/', views.deleteTodo, ),
    path('/updatetodo/<int:pk>/', views.updateTodo),

    path('', views.homePage),
    path('add/', views.addTodoPage),

]