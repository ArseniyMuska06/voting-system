# adminpanel/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

class AdminGroupRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "login_admin"  # або ім'я твого url логіну
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and u.groups.filter(name="admin").exists()