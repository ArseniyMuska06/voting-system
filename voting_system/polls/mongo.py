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
        _votes_col.create_index(
            [("poll_id", ASCENDING), ("user_id", ASCENDING)],
            unique=True,
            name="uniq_poll_user",
        )
    return _votes_col


def get_user_id_for_request(request):
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"
    if not request.session.session_key:
        request.session.save()
    return f"anon:{request.session.session_key}"

def get_user_id_for_poll(poll, request):
    base_id = get_user_id_for_request(request)
    if not getattr(poll, "is_anonymous", False):
        return base_id

    salt = getattr(settings, "ANON_VOTE_SALT", settings.SECRET_KEY)
    payload = f"{poll.pk}:{base_id}:{salt}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"anon:{digest}"