# adminpanel/forms.py
from django import forms
from django.forms import inlineformset_factory
from polls.models import Poll, PollOption


class AdminPollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = [
            "title",
            "short_description",
            "start_at",
            "end_at",
            "can_change_vote",
            "is_anonymous",        # 🔽 додати сюди
            "quorum",
            "expected_turnout",
            "status",
        ]
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean_quorum(self):
        q = self.cleaned_data["quorum"]
        if not (0 <= q <= 100):
            raise forms.ValidationError("Кворум має бути в межах 0–100%.")
        return q


class PollOptionForm(forms.ModelForm):
    class Meta:
        model = PollOption
        fields = ["text", "order"]


OptionFormSet = inlineformset_factory(
    Poll,
    PollOption,
    form=PollOptionForm,
    fields=["text", "order"],
    extra=3,          # покаже 3 порожніх рядки зверху
    min_num=2,        # мінімум 2 варіанти
    validate_min=True,
    can_delete=False,
)
