from app import db


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patron_name = db.Column(db.String(64))
    number = db.Column(db.String(32))
    pin = db.Column(db.String(16))
    last_state = db.Column(db.Text())

    def __repr__(self):
        return f"<Patron {self.patron_name}>"
