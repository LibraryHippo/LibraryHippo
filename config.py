import os
from authomatic.providers import oauth2
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, "secrets"))
load_dotenv(os.path.join(basedir, "configuration"))


class Config(object):
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 25)
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS") != "False"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")

    OAUTH = {
        "google": {
            "class_": oauth2.Google,
            "consumer_key": os.environ.get("OAUTH_GOOGLE_CLIENT_ID"),
            "consumer_secret": os.environ.get("OAUTH_GOOGLE_CLIENT_SECRET"),
            "scope": ["profile", "email"],
        }
    }

    SECRET_KEY = os.environ.get("SECRET_KEY") or "MeF`3?N',Nmsn39v]"

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
