import json
import time

from app import mail, models
from datetime import datetime
from flask_mail import Message


def register(app):
    @app.cli.command("notify-all")
    def notify_all():
        card = models.Card.query.get(1)  # a hack - we know there's only 1 card for now
        last_card_state = json.loads(card.last_state)

        html_body = "<h1>Holds</h1>"
        for hold in last_card_state["holds"]:
            html_body += "<dl>"
            for k, v in hold.items():
                html_body += f"<dt>{k}</dt><dd>{v}</dd>"
            html_body += "</dl><hr>"

        html_body += "<h1>Checkouts</h1>"
        for checkout in last_card_state["checkouts"]:
            html_body += "<dl>"
            for k, v in checkout.items():
                html_body += f"<dt>{k}</dt><dd>{v}</dd>"
            html_body += "</dl><hr>"

        now = datetime.now().isoformat()

        msg = Message(
            "LibraryHippo starting notifications", recipients=["blair@blairconrad.com"]
        )
        msg.body = f"starting notifications at {now}"
        msg.html = html_body

        mail.send(msg)

        time.sleep(300)

        now = datetime.now().isoformat()

        msg = Message(
            "LibraryHippo ending notifications", recipients=["blair@blairconrad.com"]
        )
        msg.body = f"ending notifications at {now}"
        msg.html = html_body

        mail.send(msg)
