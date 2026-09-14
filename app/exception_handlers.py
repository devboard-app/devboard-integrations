from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.exceptions import (
    IntegrationAlreadyExistsException,
    IntegrationNotFoundException,
    InvalidWebhookUrlException,
    NotificationNotFoundException,
    ProjectNotFoundException,
    RepoLinkAlreadyExistsException,
    RepoLinkNotFoundException,
)


def register_exception_handlers(app: Flask):
    @app.errorhandler(InvalidWebhookUrlException)
    def handle_invalid_webhook_url(error):
        response = jsonify({"detail": "Invalid webhook URL", "errors": None})
        response.status_code = 400
        return response

    @app.errorhandler(IntegrationAlreadyExistsException)
    def handle_integration_already_exists(error):
        response = jsonify({"detail": "Integration already exists", "errors": None})
        response.status_code = 409
        return response

    @app.errorhandler(IntegrationNotFoundException)
    def handle_integration_not_found(error):
        response = jsonify({"detail": "Integration not found", "errors": None})
        response.status_code = 404
        return response

    @app.errorhandler(RepoLinkAlreadyExistsException)
    def handle_repo_link_already_exists(error):
        response = jsonify({"detail": "Repository link already exists", "errors": None})
        response.status_code = 409
        return response

    @app.errorhandler(RepoLinkNotFoundException)
    def handle_repo_link_not_found(error):
        response = jsonify({"detail": "Repository link not found", "errors": None})
        response.status_code = 404
        return response

    @app.errorhandler(NotificationNotFoundException)
    def handle_notification_not_found(error):
        response = jsonify({"detail": "Notification not found", "errors": None})
        response.status_code = 404
        return response

    @app.errorhandler(ProjectNotFoundException)
    def handle_project_not_found(error):
        response = jsonify({"detail": "Project not found", "errors": None})
        response.status_code = 404
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        response = jsonify({"detail": error.description, "errors": None})
        response.status_code = error.code
        return response