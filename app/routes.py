import json

from app import app

from app.libraries.wpl import WPL
from app.models import Card, db


@app.route("/")
@app.route("/index")
def index():
    return "LibraryHippo 2020"


@app.route("/check")
def check():
    card = Card.query.get(1)  # a hack - we know there's only 1 card for now
    card_check_result = WPL().check_card(card)
    card.last_state = json.dumps(card_check_result)
    db.session.commit()

    result = "<h1>Holds</h1>"
    for hold in card_check_result["holds"]:
        result += "<dl>"
        for k, v in hold.items():
            result += f"<dt>{k}</dt><dd>{v}</dd>"
        result += "</dl><hr>"

    result += "<h1>Checkouts</h1>"
    for checkout in card_check_result["checkouts"]:
        result += "<dl>"
        for k, v in checkout.items():
            result += f"<dt>{k}</dt><dd>{v}</dd>"
        result += "</dl><hr>"

    return result
