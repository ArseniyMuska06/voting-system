from django.shortcuts import render
from .mongo import get_votes_collection, get_user_id_for_request
from .services import tally_poll, check_validity  # NEW

def home(request):
    return render(request, "home.html")

# polls/views.py
from django.db import models
from django.utils import timezone
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from .models import Poll
from .forms import VoteForm


def _active_filter_qs():
    now = timezone.now()
    return (Poll.objects
            .filter(status=Poll.Status.ACTIVE)
            .filter(
                # якщо start_at заданий — start_at <= now, інакше пропускаємо
                models.Q(start_at__isnull=True) | models.Q(start_at__lte=now),
            )
            .filter(
                # якщо end_at заданий — end_at >= now, інакше пропускаємо
                models.Q(end_at__isnull=True) | models.Q(end_at__gte=now),
            )
            .select_related("admin")
            .prefetch_related("options"))


from django.db import models  # потрібен для Q вище


class ActivePollListView(ListView):
    model = Poll
    template_name = "polls/list.html"
    context_object_name = "polls"

    def get_queryset(self):
        return _active_filter_qs()


class PollDetailView(DetailView):
    model = Poll
    template_name = "polls/detail.html"
    context_object_name = "poll"

    def get_queryset(self):
        # РАНІШЕ: return _active_filter_qs()   # -> лише активні (і ти ловиш 404) :contentReference[oaicite:2]{index=2}
        # ТЕПЕР: пускаємо активні АБО завершені АБО ті, в яких end_at уже минув
        now = timezone.now()
        return (Poll.objects
                .filter(
                    models.Q(status=Poll.Status.ACTIVE) |
                    models.Q(status=Poll.Status.COMPLETED) |
                    models.Q(end_at__isnull=False, end_at__lt=now)
                )
                .select_related("admin")
                .prefetch_related("options"))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VoteForm(request.POST, poll=self.object)
        if form.is_valid():
            # тут можна зберегти голос у БД — на зараз просто підтвердження
            request.session.setdefault("voted_polls", set())
            # Django session не вміє сет — тому як список:
            voted = set(request.session.get("voted_polls", []))
            voted.add(self.object.pk)
            request.session["voted_polls"] = list(voted)
            return redirect("polls:confirm", pk=self.object.pk)
        return render(request, self.template_name, {"poll": self.object, "form": form})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        poll = self.object

        # прапорець «завершене»
        now = timezone.now()
        is_finished = (
            poll.status == Poll.Status.COMPLETED or
            (poll.end_at is not None and poll.end_at <= now)
        )
        ctx["is_finished"] = is_finished

        # якщо завершене — рахуємо підсумки і (за наявності) кворум
        if is_finished:
            totals = tally_poll(poll)
            is_valid, validity_note = check_validity(poll, totals["total"])
            ctx["totals"] = totals
            ctx["is_valid"] = is_valid
            ctx["validity_note"] = validity_note
        else:
            # активне — показуємо форму, як і було
            ctx["form"] = VoteForm(poll=poll)

        return ctx
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()  # poll
        form = VoteForm(request.POST, poll=self.object)
        if not form.is_valid():
            return render(request, self.template_name, {"poll": self.object, "form": form})

        option = form.cleaned_data["option"]
        col = get_votes_collection()
        uid = get_user_id_for_request(request)
        doc_filter = {"poll_id": int(self.object.pk), "user_id": uid}

        existing = col.find_one(doc_filter)

        if existing is None:
            # перше голосування → вставляємо
            col.insert_one({
                "poll_id": int(self.object.pk),
                "user_id": uid,
                "option_id": int(option.pk),
                "created_at": timezone.now(),
                "updated_at": None,
            })
            return redirect("polls:confirm", pk=self.object.pk)

        # вже голосував
        if self.object.can_change_vote:
            # дозволено змінювати → оновлюємо варіант
            col.update_one(
                doc_filter,
                {"$set": {"option_id": int(option.pk), "updated_at": timezone.now()}}
            )
            return redirect("polls:confirm", pk=self.object.pk)
        else:
            # заборонено змінювати → показуємо помилку
            messages.error(request, "Ви вже голосували в цьому опитуванні. Змінювати голос заборонено.")
            return render(request, self.template_name, {"poll": self.object, "form": form})


def vote_confirm(request, pk):
    poll = get_object_or_404(_active_filter_qs(), pk=pk)
    messages.success(request, "Ваш голос зараховано ✅")
    # просте повідомлення + повернення на список
    return render(request, "polls/confirm.html", {"poll": poll})
