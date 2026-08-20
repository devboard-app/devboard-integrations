from flask import Flask

from app.config import settings
from app.db import db
from app.integrations.urls import integrations_bp
from app.notifications.urls import notifications_bp


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL

    db.init_app(app)

    app.register_blueprint(notifications_bp)
    app.register_blueprint(integrations_bp)
    
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
