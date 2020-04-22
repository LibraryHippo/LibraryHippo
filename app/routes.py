import json

from authomatic.adapters import WerkzeugAdapter

from flask import flash, make_response, redirect, request, session, url_for
from flask_login import current_user, login_user, logout_user

from app import app, authomatic

from app.libraries.wpl import WPL
from app.models import Card, db, User


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


@app.route("/login/<provider>/", methods=["GET", "POST"])
def login(provider):
    if not current_user.is_anonymous:
        return redirect(url_for("index"))

    response = make_response()
    result = authomatic.login(
        WerkzeugAdapter(request, response),
        provider_name=provider,
        session=session,
        session_saver=lambda: app.save_session(session, response),
    )

    if not result:
        return response

    if result.user:
        result.user.update()
        if result.user.id is None:
            flash("Authentication failed.")
            app.logger.error("Authentication failed: %s", result.error)
            return redirect(url_for("index"))

        social_id = provider + ":" + result.user.id
        user = User.query.filter_by(social_id=social_id).first()

    if not user:
        user = User(
            social_id=social_id, nickname=result.user.name, email=result.user.email
        )
        db.session.add(user)
        db.session.commit()

    login_user(user, remember=True)
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    if not current_user.is_anonymous:
        logout_user()
    return redirect(url_for("index"))
