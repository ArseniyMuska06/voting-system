from django.conf import settings
from pymongo import MongoClient

_client = None
_db = None

def get_mongo_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(settings.MONGO_URI)
        _db = _client[settings.MONGO_DB_NAME]
    return _db