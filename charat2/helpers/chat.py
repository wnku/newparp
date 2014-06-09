import json
import time

from datetime import datetime
from flask import abort, g, request
from functools import wraps
from sqlalchemy import and_, func
from sqlalchemy.orm import joinedload

from charat2.model import AnyChat, Ban, Message, ChatUser
from charat2.model.connections import db_connect, get_chat_user

def group_chat_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.chat.type!="group":
			abort(404)
        return f(*args, **kwargs)
    return decorated_function

def mark_alive(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.joining = False
        g.chat_id = int(request.form["chat_id"])
        online = g.redis.sismember("chat:%s:online" % g.chat_id, g.user_id)
        if not online:
            g.joining = True
            # XXX ONLINE USER LIMITS ETC. HERE.
            # If they've been kicked recently, don't let them in.
            if g.redis.exists("kicked:%s:%s" % (g.chat_id, g.user_id)):
                return "{\"exit\":\"kick\"}"
            # Make sure we're connected to the database for the ban checking.
            db_connect()
            # Check if we're banned.
            if g.db.query(func.count('*')).select_from(Ban).filter(and_(
                Ban.chat_id==g.chat_id,
                Ban.user_id==g.user_id,
            )).scalar() != 0:
                abort(403)
            # Get ChatUser if we haven't got it already.
            if not hasattr(g, "chat_user"):
                get_chat_user()
            # Update their last_online.
            g.chat_user.last_online = datetime.now()
            # Add them to the online list.
            g.redis.sadd("chat:%s:online" % g.chat.id, g.user.id)
            # Send join message. Or not, if they're silent.
            if g.chat_user.group == "silent":
                send_userlist(g.db, g.redis, g.chat)
            else:
                send_message(g.db, g.redis, Message(
                    chat_id=g.chat.id,
                    user_id=g.user.id,
                    type="join",
                    name=g.chat_user.name,
                    text=("[color=#%s]%s[/color] joined.") % (
                        g.chat_user.color, g.user.username,
                    ),
                ))
        g.redis.zadd(
            "chats_alive",
            time.time()+15,
            "%s/%s" % (g.chat_id, g.user_id),
        )
        return f(*args, **kwargs)
    return decorated_function

def send_message(db, redis, message):

    db.add(message)
    db.flush()

    if message.type in (u"ic", u"ooc", u"me"):

        message.chat.last_message = message.posted

        # Update last_online field for everyone who is online.
        online_user_ids = redis.smembers("chat:%s:online" % message.chat.id)
        if len(online_user_ids) != 0:
            db.query(ChatUser).filter(and_(
                ChatUser.user_id.in_(online_user_ids),
                ChatUser.chat_id == message.chat.id,
            )).update({ "last_online": message.posted }, synchronize_session=False)

    message_dict = message.to_dict()

    # Cache before sending.
    cache_key = "chat:%s" % message.chat_id
    redis.zadd(cache_key, message.id, json.dumps(message_dict))
    redis.zremrangebyrank(cache_key, 0, -51)

    # Reload userlist if necessary.
    if message.type in (
        u"join",
        u"disconnect",
        u"timeout",
        u"user_info",
        u"user_group",
        u"user_action",
    ):
        send_userlist(db, redis, message.chat)
    # Reload chat metadata if necessary.
    elif message.type == "chat_meta":
		redis.publish("channel:%s:meta" % message.chat.id, json.dumps({
		    "chat": message.chat.to_dict(),
		}))

	# And send the message.
    redis.publish("channel:%s:messages" % message.chat_id, json.dumps({
        "messages": [message_dict],
    }))

def send_userlist(db, redis, chat):
    # Update the userlist without sending a message.
    redis.publish("channel:%s:meta" % chat.id, json.dumps({
        "users": get_userlist(db, redis, chat),
    }))

def disconnect(redis, chat_id, user_id):
    redis.zrem("chats_alive", "%s/%s" % (chat_id, user_id))
    # Return True if they were in the userlist when we tried to remove them, so
    # we can avoid sending disconnection messages if someone gratuitously sends
    # quit requests.
    return (redis.srem("chat:%s:online" % chat_id, user_id) == 1)

def get_userlist(db, redis, chat):
    online_user_ids = redis.smembers("chat:%s:online" % chat.id)
    # Don't bother querying if the list is empty.
    # Also delete the message cache.
    if len(online_user_ids) == 0:
        redis.delete("chat:%s" % chat.id)
        return []
    return [
        _.to_dict() for _ in
        db.query(ChatUser).filter(and_(
            ChatUser.user_id.in_(online_user_ids),
            ChatUser.chat_id == chat.id,
        )).options(joinedload(ChatUser.user))
    ]

