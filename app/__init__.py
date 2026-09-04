import logging

from flask import Flask

from app.config import settings
from app.db import db
from app.exception_handlers import register_exception_handlers
from app.integrations.urls import integrations_bp
from app.notifications.urls import notifications_bp
from app.webhooks.urls import webhooks_bp


def create_app():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL

    db.init_app(app)
    register_exception_handlers(app)

    app.register_blueprint(notifications_bp)
    app.register_blueprint(integrations_bp)
    app.register_blueprint(webhooks_bp)
    
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
