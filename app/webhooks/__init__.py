from flask import Blueprint

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/api/webhooks")

from app.integrations import views  # noqa