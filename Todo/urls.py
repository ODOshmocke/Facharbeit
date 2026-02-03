from django.urls import path
from . import views

urlpatterns = [
    path('api/todos/', views.todos, ),
    path('api/addtodo/', views.addTodo, ),
    path('api/deletetodo/<int:pk>/', views.deleteTodo, ),
    path('api/updatetodo/<int:pk>/', views.updateTodo),

    path('', views.homePage),
    path('add/', views.addTodoPage),

]