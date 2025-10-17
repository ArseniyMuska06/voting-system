# adminpanel/urls.py
from django.urls import path
from . import views

app_name = "adminpanel"

urlpatterns = [
    path("", views.MyPollListView.as_view(), name="list"),
    path("create/", views.PollCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PollAdminDetailView.as_view(), name="detail"),
    path("<int:pk>/finish/", views.finish_now, name="finish_now"),
]
