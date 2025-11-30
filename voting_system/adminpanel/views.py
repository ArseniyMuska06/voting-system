# adminpanel/views.py
from math import ceil

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, DetailView, View

from polls.models import Poll, PollOption
from polls.mongo import get_votes_collection
from .forms import AdminPollForm, OptionFormSet

from .mixins import AdminGroupRequiredMixin


def _quorum_required(poll: Poll) -> int | None:
    """
    Скільки голосів потрібно, щоб кворум вважався досягнутим.
    Якщо expected_turnout не заданий → повертаємо None (не можна визначити).
    """
    if poll.expected_turnout is None:
        return None
    return ceil(poll.expected_turnout * (poll.quorum / 100.0))


def _votes_count_for_poll(poll_id: int) -> int:
    col = get_votes_collection()
    return col.count_documents({"poll_id": int(poll_id)})


def _option_counts(poll: Poll) -> dict[int, int]:
    """Повертає {option_id: votes} по всіх варіантах опитування."""
    col = get_votes_collection()
    result = {}
    for opt in poll.options.all():
        c = col.count_documents({"poll_id": int(poll.pk), "option_id": int(opt.pk)})
        result[int(opt.pk)] = c
    return result

def _is_poll_finished(poll: Poll) -> bool:
    """
    Вважаємо опитування завершеним, якщо:
    - статус COMPLETED, або
    - end_at заданий і вже минув.
    """
    now = timezone.now()
    return (
        poll.status == Poll.Status.COMPLETED
        or (poll.end_at is not None and poll.end_at <= now)
    )

class MyPollListView(AdminGroupRequiredMixin, ListView):
    """
    /adminpanel/ — список моїх голосувань (admin = поточний юзер).
    Картки з назвою/датами/статусом.
    """
    model = Poll
    template_name = "adminpanel/list.html"
    context_object_name = "polls"
    paginate_by = 20

    def get_queryset(self):
        return (
            Poll.objects.filter(admin=self.request.user)
            .select_related("admin")
            .prefetch_related("options")
            .order_by("-created_at")
        )


class PollCreateView(AdminGroupRequiredMixin, View):
    """
    /adminpanel/create/ — створення Poll + PollOption (мін. 2).
    """
    template_name = "adminpanel/create.html"
    success_url = reverse_lazy("adminpanel:list")

    def get(self, request):
        poll_form = AdminPollForm(initial={"status": Poll.Status.DRAFT})
        formset = OptionFormSet()
        return render(
            request,
            self.template_name,
            {"poll_form": poll_form, "formset": formset},
        )

    def post(self, request):
        poll_form = AdminPollForm(request.POST)
        formset = OptionFormSet(request.POST)

        if not (poll_form.is_valid() and formset.is_valid()):
            messages.error(request, "Перевірте форму: є помилки.")
            return render(
                request,
                self.template_name,
                {"poll_form": poll_form, "formset": formset},
            )

        with transaction.atomic():
            poll: Poll = poll_form.save(commit=False)
            poll.admin = request.user
            poll.save()
            formset.instance = poll
            formset.save()

        messages.success(request, "Голосування створено.")
        return redirect(self.success_url)


class PollAdminDetailView(AdminGroupRequiredMixin, DetailView):
    """
    /adminpanel/<poll_id>/ — перегляд як у користувача + службова інфа:
    - загальна кількість голосів (Mongo)
    - дійсність за кворумом
    - кнопка «Завершити зараз» (POST)
    """
    model = Poll
    template_name = "adminpanel/detail.html"
    context_object_name = "poll"

    def get_queryset(self):
        # тільки свої опитування
        return Poll.objects.filter(admin=self.request.user).prefetch_related("options")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        poll: Poll = self.object

        total_votes = _votes_count_for_poll(poll.pk)
        need_votes = _quorum_required(poll)
        is_finished = _is_poll_finished(poll)

        # 🔐 Результати по варіантах:
        # - для НЕанонімних показуємо завжди
        # - для анонімних — лише після завершення
        option_votes = None
        if (not poll.is_anonymous) or is_finished:
            option_votes = _option_counts(poll)

        # дійсність (valid)
        if poll.quorum == 0:
            valid = True
        elif need_votes is None:
            valid = None  # не можемо визначити без expected_turnout
        else:
            valid = total_votes >= need_votes

        ctx.update(
            {
                "total_votes": total_votes,
                "option_votes": option_votes,  # dict {option_id: count}
                "need_votes": need_votes,
                "valid": valid,
                "now": timezone.now(),
                "is_finished": is_finished,    # 🔽 нове
            }
        )
        return ctx


def finish_now(request, pk: int):
    """
    POST /adminpanel/<pk>/finish/ — встановити end_at=now, status=COMPLETED.
    """
    if request.method != "POST":
        return redirect(reverse("adminpanel:detail", args=[pk]))

    poll = get_object_or_404(Poll, pk=pk, admin=request.user)
    poll.end_at = timezone.now()
    poll.status = Poll.Status.COMPLETED
    poll.save(update_fields=["end_at", "status", "updated_at"])
    messages.success(request, "Голосування завершене зараз.")
    return redirect(reverse("adminpanel:detail", args=[pk]))
