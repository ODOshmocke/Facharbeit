from django.urls import path

from .views import SignUpView
from .views import login_view, logout_view

# accounts/urls.py
urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", login_view, name="login"),  # Die View aus der vorherigen Antwort
    path("logout/", logout_view, name="logout"),
]