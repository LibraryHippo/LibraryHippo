from flask import current_app
from authomatic.adapters import WerkzeugAdapter
from flask import (
    flash,
    make_response,
    redirect,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_user, logout_user
from app import authomatic, db
from app.auth import bp
from app.models import User


@bp.route("/login/<provider>/", methods=["GET", "POST"])
def login(provider):
    if not current_user.is_anonymous:
        return redirect(url_for("main.index"))

    response = make_response()
    result = authomatic.login(
        WerkzeugAdapter(request, response),
        provider_name=provider,
        session=session,
        session_saver=lambda: current_app.save_session(session, response),
    )

    if not result:
        return response

    if result.user:
        result.user.update()
        if result.user.id is None:
            flash("Authentication failed.")
            current_app.logger.error("Authentication failed: %s", result.error)
            return redirect(url_for("main.welcome"))

        social_id = provider + ":" + result.user.id
        user = User.query.filter_by(social_id=social_id).first()

    if not user:
        user = User(
            social_id=social_id, nickname=result.user.name, email=result.user.email
        )
        db.session.add(user)
        db.session.commit()

    login_user(user, remember=True)
    return redirect(url_for("main.index"))


@bp.route("/logout")
def logout():
    if not current_user.is_anonymous:
        logout_user()
    return redirect(url_for("main.welcome"))
