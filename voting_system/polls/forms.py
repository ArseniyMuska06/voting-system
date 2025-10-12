# polls/forms.py
from django import forms
from .models import PollOption

class VoteForm(forms.Form):
    option = forms.ModelChoiceField(
        queryset=PollOption.objects.none(),
        widget=forms.RadioSelect,
        empty_label=None,
        label="Оберіть варіант"
    )

    def __init__(self, *args, **kwargs):
        poll = kwargs.pop("poll")
        super().__init__(*args, **kwargs)
        self.fields["option"].queryset = poll.options.all()
