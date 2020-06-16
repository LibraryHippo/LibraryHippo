from logging.config import dictConfig
import os

from authomatic import Authomatic
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

login_manager = LoginManager()
mail = Mail()
db = SQLAlchemy()
migrate = Migrate()
authomatic = Authomatic(config=None, secret=None)


def create_app(config_class=Config):

    if not os.path.exists("logs"):
        os.mkdir("logs")

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "default": {
                    "format": (
                        "%(asctime)s %(levelname)s: %(message)s"
                        " [in %(pathname)s:%(lineno)d]"
                    )
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://flask.logging.wsgi_errors_stream",
                    "formatter": "default",
                    "level": "INFO",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "logs/libraryhippo.log",
                    "maxBytes": 1024000,
                    "backupCount": 10,
                    "formatter": "default",
                    "level": "DEBUG",
                },
            },
            "root": {"level": "DEBUG", "handlers": ["wsgi", "file"]},
        }
    )

    app = Flask(__name__)
    app.config.from_object(config_class)

    login_manager.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    authomatic.config = config_class.OAUTH
    authomatic.secret = config_class.SECRET_KEY

    app.logger.info("LibraryHippo startup")

    from . import auth  # noqa - imports at bottom to avoid circular references
    from . import main  # noqa - imports at bottom to avoid circular references

    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)

    return app


from app import models  # noqa - imports at bottom to avoid circular references
