from django.contrib import admin
from django.urls import path, include
from polls.views import home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("accounts/", include("accounts.urls")),
    path("polls/", include("polls.urls")),
]
