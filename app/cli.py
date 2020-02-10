import time

from app import mail
from datetime import datetime
from flask_mail import Message


def register(app):
    @app.cli.command("notify-all")
    def notify_all():
        now = datetime.now().isoformat()

        msg = Message(
            "LibraryHippo starting notifications", recipients=["blair@blairconrad.com"]
        )
        msg.body = f"starting notifications at {now}"
        msg.html = f"<h1>Test mail from LibraryHippo</h1><p>{msg.body}."

        print(msg.body)
        mail.send(msg)

        time.sleep(300)

        now = datetime.now().isoformat()

        msg = Message(
            "LibraryHippo ending notifications", recipients=["blair@blairconrad.com"]
        )
        msg.body = f"ending notifications at {now}"
        msg.html = f"<h1>Test mail from LibraryHippo</h1><p>{msg.body}."

        print(msg.body)
        mail.send(msg)
