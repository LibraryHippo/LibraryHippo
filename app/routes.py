from app import app
from config import Config

from app.libraries.wpl import WPL


@app.route("/")
@app.route("/index")
def index():
    return "LibraryHippo 2020"


@app.route("/check")
def check():
    return WPL().check_card(Config.PATRON_NAME, Config.CARD_NUMBER, Config.PIN)
