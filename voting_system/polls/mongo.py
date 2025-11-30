# polls/mongo.py
from django.conf import settings
from pymongo import MongoClient, ASCENDING
import hashlib

_client = None
_votes_col = None

def get_votes_collection():
    global _client, _votes_col
    if _votes_col is None:
        _client = MongoClient(settings.MONGODB_URI)
        db = _client[settings.MONGODB_DB_NAME]
        _votes_col = db[settings.MONGODB_VOTES_COLLECTION]
        # індекс унікальності (idempotent — створиться один раз)
        _votes_col.create_index(
            [("poll_id", ASCENDING), ("user_id", ASCENDING)],
            unique=True,
            name="uniq_poll_user",
        )
    return _votes_col


def get_user_id_for_request(request):
    """
    Визначаємо user_id:
    - якщо користувач залогінений — беремо його pk;
    - інакше — використовуємо session key як псевдо-ідентифікатор.
    """
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"
    # гарантуємо наявність session_key
    if not request.session.session_key:
        request.session.save()
    return f"anon:{request.session.session_key}"

def get_user_id_for_poll(poll, request):
    """
    Повертає значення поля user_id для документа голосу в MongoDB.

    - Якщо poll.is_anonymous == False → як і раніше:
        * авторизований: "user:<pk>"
        * неавторизований: "anon:<session_key>"

    - Якщо poll.is_anonymous == True → детермінований хеш:
        "anon:<sha256(poll_id + base_id + ANON_VOTE_SALT)>"
        де base_id = user:<pk> або anon:<session_key>.

    Таким чином:
      • у Mongo НЕ видно реальний user_id;
      • але той самий користувач у тому ж опитуванні завжди дає той самий хеш → можна ловити повторне голосування.
    """
    base_id = get_user_id_for_request(request)  # "user:5" або "anon:<session_key>"
    if not getattr(poll, "is_anonymous", False):
        return base_id

    salt = getattr(settings, "ANON_VOTE_SALT", settings.SECRET_KEY)
    payload = f"{poll.pk}:{base_id}:{salt}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"anon:{digest}"