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


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
