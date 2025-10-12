# polls/mongo.py
from django.conf import settings
from pymongo import MongoClient, ASCENDING

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
