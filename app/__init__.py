from flask import Flask

from app.config import settings
from app.db import db


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URL

    db.init_app(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
