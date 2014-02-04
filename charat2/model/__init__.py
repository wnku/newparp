from sqlalchemy import create_engine
from sqlalchemy.schema import Index
from sqlalchemy.orm import relation, scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    ForeignKey,
    Boolean,
    DateTime,
    Enum,
    Integer,
    String,
    Unicode,
    UnicodeText,
)

import datetime

engine = create_engine(
    # XXX GET THIS FROM CONFIG OR ENVIRON OR SOMETHING
    'sqlite:////tmp/test.db',
    convert_unicode=True,
    pool_recycle=3600,
)

sm = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

base_session = scoped_session(sm)

Base = declarative_base()
Base.query = base_session.query_property()

def init_db():
    engine.echo = True
    Base.metadata.create_all(bind=engine)

def now():
    return datetime.datetime.now()

case_options = Enum(
    u"alt-lines",
    u"alternating",
    u"inverted",
    u"lower",
    u"normal",
    u"title",
    u"upper",
    name=u"case",
)


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    # Username must be alphanumeric.
    username = Column(String(50), unique=True)

    # Bcrypt hash.
    password = Column(String(60), nullable=False)

    group = Column(Enum(
        u"guest",
        u"active",
        u"admin",
        u"banned",
        name=u"users_group",
    ), nullable=False, default=u"guest")

    created = Column(DateTime(), nullable=False, default=now)
    last_online = Column(DateTime(), nullable=False, default=now)

    # Global character data. This is copied whenever a UserChat is created.

    name = Column(Unicode(50), nullable=False, default=u"Anonymous")
    acronym = Column(Unicode(15), nullable=False, default=u"")

    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default=u"000000")

    quirk_prefix = Column(Unicode(50), nullable=False, default=u"")
    quirk_suffix = Column(Unicode(50), nullable=False, default=u"")

    case = Column(case_options, nullable=False, default=u"normal")

    replacements = Column(UnicodeText, nullable=False, default=u"[]")

    confirm_disconnect = Column(Boolean, nullable=False, default=False)
    show_system_messages = Column(Boolean, nullable=False, default=True)
    show_topic = Column(Boolean, nullable=False, default=True)
    show_bbcode = Column(Boolean, nullable=False, default=True)
    desktop_notifications = Column(Boolean, nullable=False, default=False)


class Chat(Base):

    __tablename__ = "chats"
    __mapper_args__ = { "polymorphic_on": "type" }

    id = Column(Integer, primary_key=True)

    # URL must be alphanumeric. It must normally be capped to 50 characters,
    # but sub-chats are prefixed with the parent URL and a slash, so we need
    # 101 characters to fit 50 characters in each half.
    url = Column(String(101), unique=True)

    # 1-on-1 chats allow anyone to enter and have randomly generated URLs.
    # Group chats allow people to enter in accordance with the publicity
    # options in the group_chats table, and can have any URL.
    # PM chats only allow two people to enter and have urls of the form
    # `pm/<user id 1>/<user id 2>`, with the 2 user IDs in alphabetical
    # order.
    type = Column(Enum(
        u"1-on-1",
        u"group",
        u"pm",
        name=u"chats_type",
    ), nullable=False, default=u"group")

    created = Column(DateTime(), nullable=False, default=now)

    # Last message time should only update when users send messages, not system
    # messages.
    last_message = Column(DateTime(), nullable=False, default=now)


class OneOnOneChat(Chat):
    __mapper_args__ = { "polymorphic_identity": "1-on-1" }


class GroupChat(Chat):

    __tablename__ = "group_chats"

    id = Column(Integer, ForeignKey("chats.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "group",
        "inherit_condition": id==Chat.id,
    }

    topic = Column(UnicodeText, nullable=False, default=u"")

    autosilence = Column(Boolean, nullable=False, default=False)
    nsfw = Column(Boolean, nullable=False, default=False)

    publicity = Column(Enum(
        u"listed",
        u"unlisted",
        name=u"group_chats_publicity",
    ), nullable=False, default=u"unlisted")

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("chats.id"), nullable=False)


class PMChat(Chat):
    __mapper_args__ = { "polymorphic_identity": "pm" }


class UserChat(Base):

    __tablename__ = "user_chats"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), primary_key=True)

    last_online = Column(DateTime(), nullable=False, default=now)

    # Ignored if the user is an admin or the chat's creator.
    group = Column(Enum(
        u"mod",
        u"mod2",
        u"mod3",
        u"silent",
        u"user",
        name=u"user_chats_group",
    ), nullable=False, default=u"user")

    name = Column(Unicode(50), nullable=False, default=u"Anonymous")
    acronym = Column(Unicode(15), nullable=False, default=u"")

    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default=u"000000")

    quirk_prefix = Column(Unicode(50), nullable=False, default=u"")
    quirk_suffix = Column(Unicode(50), nullable=False, default=u"")

    case = Column(case_options, nullable=False, default=u"normal")

    replacements = Column(UnicodeText, nullable=False, default=u"[]")

    confirm_disconnect = Column(Boolean, nullable=False, default=False)
    show_system_messages = Column(Boolean, nullable=False, default=True)
    show_topic = Column(Boolean, nullable=False, default=True)
    show_bbcode = Column(Boolean, nullable=False, default=True)
    desktop_notifications = Column(Boolean, nullable=False, default=False)


class Message(Base):

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)

    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)

    # Can be null because system messages aren't associated with a user.
    user_id = Column(Integer, ForeignKey("users.id"))

    posted = Column(DateTime(), nullable=False, default=now)

    # XXX CONSIDER SPLITTING SYSTEM INTO USER_CHANGE, META_CHANGE ETC.
    type = Column(Enum(
        u"ic",
        u"ooc",
        u"system",
        name=u"messages_type",
    ), nullable=False, default=u"ic")

    # Must be a hex code.
    color = Column(Unicode(6), nullable=False, default=u"000000")

    acronym = Column(Unicode(50), nullable=False, default=u"")

    text = Column(UnicodeText, nullable=False)


# Index to make generating the public chat list easier.
# This is a partial index, a feature only supported by Postgres, so I don't
# know what will happen if you try to run this on anything else.
Index(
    "group_chats_publicity_listed",
    GroupChat.publicity,
    postgresql_where=GroupChat.publicity==u"listed",
)

# Index to make log rendering easier.
Index("messages_chat_id", Message.chat_id, Message.posted)


GroupChat.creator = relation(User, backref='created_chats')
GroupChat.parent = relation(
    Chat,
    backref='children',
    primaryjoin=GroupChat.parent_id==Chat.id,
)

UserChat.user = relation(User, backref='chats')
UserChat.chat = relation(Chat, backref='users')

Message.chat = relation(User)
Message.user = relation(Chat)

