from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # створюємо групу admin після міграцій
        from django.db.models.signals import post_migrate
        from django.contrib.auth.models import Group

        def ensure_group(sender, **kwargs):
            Group.objects.get_or_create(name="admin")
        post_migrate.connect(ensure_group, sender=self)