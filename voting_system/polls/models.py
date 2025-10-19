from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Poll(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    title = models.CharField(max_length=200)                    # Назва
    short_description = models.CharField(max_length=500, blank=True)  # Короткий опис
    start_at = models.DateTimeField(null=True, blank=True)      # Дата початку
    end_at = models.DateTimeField(null=True, blank=True)        # Дата закінчення
    can_change_vote = models.BooleanField(default=False)        # дозволяти/ні зміну голосу
    quorum = models.PositiveSmallIntegerField(                  # кворум у %, 0–100
        help_text="Кворум у відсотках (0–100).",
    )
    expected_turnout = models.PositiveIntegerField(null=True, blank=True, help_text="Очікуваний корпус виборців (шт.).")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    admin = models.ForeignKey(                                  # власник (admin_id)
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_polls",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def clean(self):
        super().clean()
        if self.start_at and self.end_at and self.start_at >= self.end_at:
            raise ValidationError({"end_at": "Кінець має бути пізніше за початок."})

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quorum__gte=0) & models.Q(quorum__lte=100),
                name="poll_quorum_between_0_and_100",
            )
        ]


class PollOption(models.Model):
    poll = models.ForeignKey(
        'Poll',
        on_delete=models.CASCADE,
        related_name='options',
    )
    text = models.CharField(max_length=300)
    order = models.PositiveIntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # якщо order не заданий вручну — призначити наступний номер
        if self.order is None:
            last_option = PollOption.objects.filter(poll=self.poll).order_by('-order').first()
            self.order = 1 if last_option is None else last_option.order + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.order}] {self.text}"

    class Meta:
        ordering = ["poll_id", "order"]
        unique_together = [("poll", "order")]

