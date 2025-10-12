from django.shortcuts import render
from accounts.decorator import admin_required

@admin_required
def dashboard(request):
    return render(request, "adminpanel/dashboard.html")