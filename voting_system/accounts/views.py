""" from django.shortcuts import render

# Create your views here.
 """

from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from .forms import UserRegisterForm, UserProfileForm, AdminProfileForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import logout
import re

def register_user(request):
    if request.method == "POST":
        uform = UserRegisterForm(request.POST)
        pform = UserProfileForm(request.POST)
        if uform.is_valid() and pform.is_valid():
            user = uform.save()
            profile = pform.save(commit=False)
            profile.user = user
            profile.save()
            login(request, user)
            return redirect("/polls/")
    else:
        uform = UserRegisterForm()
        pform = UserProfileForm()
    return render(request, "accounts/register_user.html", {"uform": uform, "pform": pform})

def register_admin(request):
    if request.method == "POST":
        uform = UserRegisterForm(request.POST)
        pform = AdminProfileForm(request.POST)
        if uform.is_valid() and pform.is_valid():
            password = uform.cleaned_data.get("password1")

            """ if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
                messages.error(request, "Пароль не повинен містити спеціальних символів (!@#$%^&* тощо), оскільки не зможете пройти далі")
                return render(request, "accounts/register_admin.html", {"uform": uform, "pform": pform}) """

            user = uform.save()
            profile = pform.save(commit=False)
            profile.user = user
            profile.save()
            # додаємо у групу "admin"
            admin_group = Group.objects.get(name="admin")
            user.groups.add(admin_group)
            login(request, user)
            return redirect("/adminpanel/")
    else:
        uform = UserRegisterForm()
        pform = AdminProfileForm()
    return render(request, "accounts/register_admin.html", {"uform": uform, "pform": pform})

class UserLoginView(LoginView):
    template_name = "accounts/login_user.html"
    redirect_authenticated_user = False  # щоб не редіректило, якщо вже залогінений

    def form_valid(self, form):
        user = form.get_user()
        # ❗ Перевіряємо, що користувач НЕ є адміністратором
        if user.groups.filter(name="admin").exists():
            form.add_error(None, "Цей акаунт належить адміністратору. Увійди через сторінку для адмінів.")
            return self.form_invalid(form)
        # якщо звичайний користувач — виконуємо стандартний логін
        return super().form_valid(form)

    def get_success_url(self):
        return "/polls/"

class AdminLoginView(LoginView):
    template_name = "accounts/login_admin.html"
    redirect_authenticated_user = False  # щоб уже залогіненого юзера не редіректило автоматично

    def form_valid(self, form):
        user = form.get_user()
        # ❗ Перевіряємо членство в групі 'admin'
        if not user.groups.filter(name="admin").exists():
            # НЕ викликаємо super().form_valid(form), щоб не логінити
            form.add_error(None, "Немає прав адміністратора. Увійди як адмін або скористайся звичайним входом.")
            return self.form_invalid(form)
        # якщо адмін — тоді стандартний логін і редірект
        return super().form_valid(form)

    def get_success_url(self):
        return "/adminpanel/"