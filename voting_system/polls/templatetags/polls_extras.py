# polls/templatetags/polls_extras.py
from django import template
from polls.mongo import get_votes_collection, get_user_id_for_request

register = template.Library()

@register.simple_tag(takes_context=True)
def has_voted(context, poll):
    """
    True якщо поточний користувач уже голосував у цьому poll (MongoDB).
    """
    request = context.get("request")
    if request is None or poll is None:
        return False
    try:
        col = get_votes_collection()
        uid = get_user_id_for_request(request)
        doc_filter = {"poll_id": int(poll.pk), "user_id": uid}
        return col.find_one(doc_filter) is not None
    except Exception:
        return False
