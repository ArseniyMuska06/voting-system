from django.contrib import admin
from .models import Poll, PollOption


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2  # скільки пустих рядків показувати для швидкого додавання
    fields = ("order", "text")


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "quorum", "start_at", "end_at", "admin")
    list_filter = ("status", "admin")
    search_fields = ("title", "short_description")
    inlines = [PollOptionInline]


@admin.register(PollOption)
class PollOptionAdmin(admin.ModelAdmin):
    list_display = ("id", "poll", "order", "text")
    list_filter = ("poll",)
    search_fields = ("text",)
