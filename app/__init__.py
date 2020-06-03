from logging.config import dictConfig
import os

from authomatic import Authomatic
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

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
app.config.from_object(Config)

login_manager = LoginManager(app)
mail = Mail(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

authomatic = Authomatic(config=Config.OAUTH, secret=Config.SECRET_KEY)

app.logger.info("LibraryHippo startup")

from app import routes, models  # noqa - imports at bottom to avoid circular references
