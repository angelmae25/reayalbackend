# =============================================================================
# app/models/models.py  —  SQLAlchemy ORM models (mirror of Schoolifetrue_db.sql)
# =============================================================================

from datetime import datetime
from .. import db


# ─────────────────────────────────────────────────────────────────────────────
# STUDENT
# ─────────────────────────────────────────────────────────────────────────────
class Student(db.Model):
    __tablename__ = 'students'

    id            = db.Column(db.Integer,     primary_key=True)
    student_id    = db.Column(db.String(30),  nullable=False, unique=True)
    first_name    = db.Column(db.String(80),  nullable=False)
    last_name     = db.Column(db.String(80),  nullable=False)
    email         = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    course        = db.Column(db.String(100), default='')
    year_level    = db.Column(db.String(30),  default='1st Year')
    contact       = db.Column(db.String(20),  nullable=True)
    avatar_url    = db.Column(db.String(300), nullable=True)
    points        = db.Column(db.Integer,     default=0)
    status        = db.Column(db.Enum('PENDING', 'ACTIVE', 'INACTIVE'), default='PENDING')
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    marketplace_items = db.relationship('MarketplaceItem', backref='seller',   lazy=True)
    lost_found_items  = db.relationship('LostFound',       backref='reporter', lazy=True)
    sent_messages     = db.relationship('Message',         backref='sender',   lazy=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self, rank=None):
        return {
            'id':         self.id,
            'student_id': self.student_id,
            'full_name':  self.full_name,
            'email':      self.email,
            'course':     self.course,
            'year_level': self.year_level,
            'contact':    self.contact,
            'avatar_url': self.avatar_url,
            'points':     self.points,
            'status':     self.status,
            'rank':        rank or 0,
            'club_count': len(self.memberships),
            'post_count': 0,
        }


# ─────────────────────────────────────────────────────────────────────────────
# NEWS
# ─────────────────────────────────────────────────────────────────────────────
class News(db.Model):
    __tablename__ = 'news'

    id           = db.Column(db.Integer,     primary_key=True)
    title        = db.Column(db.String(255), nullable=False)
    body         = db.Column(db.Text,        nullable=False)
    category     = db.Column(db.Enum('all','health','academic','campus','sports'), default='all')
    published_at = db.Column(db.DateTime,    default=datetime.utcnow)
    is_featured  = db.Column(db.Boolean,     default=False)
    image_url    = db.Column(db.String(300), nullable=True)
    author_name  = db.Column(db.String(100), default='Scholife Editorial')
    created_at   = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':           str(self.id),
            'title':        self.title,
            'body':         self.body,
            'category':     self.category,
            'published_at': self.published_at.isoformat(),
            'is_featured':  self.is_featured,
            'image_url':    self.image_url,
            'author_name':  self.author_name,
        }


# ─────────────────────────────────────────────────────────────────────────────
# EVENT
# ─────────────────────────────────────────────────────────────────────────────
class Event(db.Model):
    __tablename__ = 'events'

    id          = db.Column(db.Integer,     primary_key=True)
    short_name  = db.Column(db.String(20),  nullable=False)
    full_name   = db.Column(db.String(255), nullable=False)
    date        = db.Column(db.Date,        nullable=False)
    venue       = db.Column(db.String(150), default='')
    category    = db.Column(db.String(50),  default='General')
    color       = db.Column(db.String(10),  default='#8B1A1A')
    description = db.Column(db.Text,        nullable=True)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':          str(self.id),
            'short_name':  self.short_name,
            'full_name':   self.full_name,
            'date':        self.date.isoformat(),
            'venue':       self.venue,
            'category':    self.category,
            'color':       self.color,
            'description': self.description,
        }


# ─────────────────────────────────────────────────────────────────────────────
# CLUB
# ─────────────────────────────────────────────────────────────────────────────
club_memberships = db.Table(
    'club_memberships',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id'), primary_key=True),
    db.Column('club_id',    db.Integer, db.ForeignKey('clubs.id'),    primary_key=True),
    db.Column('joined_at',  db.DateTime, default=datetime.utcnow),
)

Student.memberships = db.relationship(
    'Club', secondary=club_memberships,
    backref=db.backref('members', lazy='dynamic')
)


class Club(db.Model):
    __tablename__ = 'clubs'

    id          = db.Column(db.Integer,     primary_key=True)
    name        = db.Column(db.String(150), nullable=False)
    acronym     = db.Column(db.String(20),  default='')
    department  = db.Column(db.String(100), default='')
    description = db.Column(db.Text,        nullable=True)
    icon_name   = db.Column(db.String(50),  default='groups')
    color       = db.Column(db.String(10),  default='#8B1A1A')
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self, is_joined=False):
        return {
            'id':           str(self.id),
            'name':         self.name,
            'acronym':      self.acronym,
            'department':   self.department,
            'description':  self.description,
            'icon_name':    self.icon_name,
            'color':        self.color,
            'is_joined':    is_joined,
            'member_count': self.members.count(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# MARKETPLACE
# NOTE: image_url is db.Text to support base64 data URIs
# Run once in MySQL: ALTER TABLE marketplace_items MODIFY COLUMN image_url LONGTEXT;
# ─────────────────────────────────────────────────────────────────────────────
class MarketplaceItem(db.Model):
    __tablename__ = 'marketplace_items'

    id          = db.Column(db.Integer,       primary_key=True)
    name        = db.Column(db.String(150),   nullable=False)
    description = db.Column(db.Text,          nullable=True)
    condition_  = db.Column('condition_', db.String(60), default='Good condition')
    price       = db.Column(db.Numeric(10,2), nullable=False, default=0)
    image_url   = db.Column(db.Text,          nullable=True)
    seller_id   = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    is_sold     = db.Column(db.Boolean,       default=False)
    posted_at   = db.Column(db.DateTime,      default=datetime.utcnow)

    def to_dict(self):
        s = self.seller
        return {
            'id':          str(self.id),
            'name':        self.name,
            'description': self.description,
            'condition':   self.condition_,
            'price':       float(self.price),
            'image_url':   self.image_url,
            'seller_id':   str(self.seller_id),
            'seller_name': s.full_name if s else '',
            'is_sold':     self.is_sold,
            'posted_at':   self.posted_at.isoformat(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# LOST & FOUND
# ─────────────────────────────────────────────────────────────────────────────
class LostFound(db.Model):
    __tablename__ = 'lost_found'

    id          = db.Column(db.Integer,     primary_key=True)
    title       = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text,        nullable=True)
    location    = db.Column(db.String(150), default='')
    date        = db.Column(db.Date,        nullable=False)
    status      = db.Column(db.Enum('lost','found'), default='lost')
    reporter_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    image_url   = db.Column(db.String(300), nullable=True)
    is_resolved = db.Column(db.Boolean,     default=False)
    created_at  = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':          str(self.id),
            'title':       self.title,
            'description': self.description,
            'location':    self.location,
            'date':        self.date.isoformat(),
            'status':      self.status,
            'reporter_id': str(self.reporter_id),
            'image_url':   self.image_url,
            'is_resolved': self.is_resolved,
        }


# ─────────────────────────────────────────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────────────────────────────────────────
conv_members = db.Table(
    'conversation_members',
    db.Column('conversation_id', db.Integer, db.ForeignKey('conversations.id'), primary_key=True),
    db.Column('student_id',      db.Integer, db.ForeignKey('students.id'),      primary_key=True),
)


class Conversation(db.Model):
    __tablename__ = 'conversations'

    id         = db.Column(db.Integer,     primary_key=True)
    name       = db.Column(db.String(150), nullable=True)
    is_group   = db.Column(db.Boolean,     default=False)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    members  = db.relationship('Student',  secondary=conv_members, backref='conversations')
    messages = db.relationship('Message',  backref='conversation', lazy=True,
                               order_by='Message.sent_at')

    def last_message(self):
        if self.messages:
            return self.messages[-1]
        return None

    def to_dict(self, current_student_id=None):
        last = self.last_message()
        return {
            'id':              str(self.id),
            'name':            self.name or '',
            'is_group':        self.is_group,
            'last_message':    last.text if last else '',
            'last_message_at': last.sent_at.isoformat() if last else self.created_at.isoformat(),
            'unread_count':    0,
        }


class Message(db.Model):
    __tablename__ = 'messages'

    id              = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id       = db.Column(db.Integer, db.ForeignKey('students.id'),      nullable=False)
    text            = db.Column(db.Text,    nullable=False)
    sent_at         = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, current_student_id=None):
        return {
            'id':        str(self.id),
            'text':      self.text,
            'sender_id': str(self.sender_id),
            'sent_at':   self.sent_at.isoformat(),
            'is_mine':   (self.sender_id == current_student_id),
        }