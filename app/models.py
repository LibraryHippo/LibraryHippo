import datetime

from app import db, login_manager
from flask_login import UserMixin


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patron_name = db.Column(db.String(64))
    number = db.Column(db.String(32))
    pin = db.Column(db.String(16))
    last_state = db.Column(db.Text())

    def __repr__(self):
        return f"<Patron {self.patron_name}>"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)


class Hold:
    def __init__(self):
        self.patron_name = ""
        self.title = ""
        self.author = ""
        self.url = ""
        self.status = ""
        self.status_notes = []
        self.expires = datetime.date.max
        self.pickup = ""


class Checkout:
    def __init__(self):
        self.patron_name = ""
        self.library_name = ""
        self.title = ""
        self.author = ""
        self.url = ""
        self.due_date = ""
        self.status_notes = []


class CardCheckResult:
    def __init__(self, holds, checkouts):
        self.holds = holds
        self.checkouts = checkouts


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
