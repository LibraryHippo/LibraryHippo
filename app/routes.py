from app import app
from app import mail
from datetime import datetime
from flask_mail import Message


@app.route("/")
@app.route("/index")
def index():
    return "LibraryHippo 2020"


@app.route("/sendmail")
def sendmail():
    now = datetime.now().strftime("%c")
    msg = Message("Mail from LibraryHippo", recipients=["blair@blairconrad.com"])
    msg.body = f"test mail from LibraryHippo at {now}"
    msg.html = f"<h1>Test mail from LibraryHippo</h1><p>It's now {now}."
    mail.send(msg)
    return f"Sent mail at {now}"
