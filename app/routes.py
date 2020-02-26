from app import app
from config import Config

from app.libraries.wpl import WPL


@app.route("/")
@app.route("/index")
def index():
    return "LibraryHippo 2020"


@app.route("/check")
def check():
    card_check_result = WPL().check_card(
        Config.PATRON_NAME, Config.CARD_NUMBER, Config.PIN
    )

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
