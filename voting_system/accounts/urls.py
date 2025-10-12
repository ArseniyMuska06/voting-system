from django.urls import path
from . import views
from .views import UserLoginView, AdminLoginView

urlpatterns = [
    path("register/", views.register_user, name="register_user"),
    path("register-admin/", views.register_admin, name="register_admin"),
    path("login/", UserLoginView.as_view(), name="login_user"),
    path("login-admin/", AdminLoginView.as_view(), name="login_admin"),
]
