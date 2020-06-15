import datetime
import json

from flask import render_template

from app.libraries.wpl import WPL
from app.models import Card, db
from app.main import bp


@bp.route("/welcome")
def welcome():
    return render_template("welcome.jinja")


@bp.route("/")
@bp.route("/index")
def index():
    card = Card.query.get(1)  # a hack - we know there's only 1 card for now
    card_check_result = WPL().check_card(card)
    card.last_state = to_json(card_check_result)
    db.session.commit()

    return render_template("index.jinja", status=card_check_result)


class JSONEncoder(json.JSONEncoder):
    def default(self, object):
        if isinstance(object, datetime.date):
            return object.strftime("%Y-%m-%d")
        elif hasattr(object, "__dict__"):
            return object.__dict__
        return json.JSONEncoder.default(self, object)


def to_json(object):
    return JSONEncoder().encode(object)
