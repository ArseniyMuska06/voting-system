# polls/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = "polls"

urlpatterns = [
    path("", views.ActivePollListView.as_view(), name="list"),
    path("<int:pk>/", views.PollDetailView.as_view(), name="detail"),
    path("<int:pk>/confirm/", views.vote_confirm, name="confirm"),
    path("logout/", LogoutView.as_view(next_page="/"), name="logout"),
]