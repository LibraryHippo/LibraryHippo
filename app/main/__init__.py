from flask import Blueprint

bp = Blueprint("main", __name__)

from app.main import routes  # noqa - imports at bottom to avoid circular references
