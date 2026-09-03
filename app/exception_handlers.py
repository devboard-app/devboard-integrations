from flask import Flask, jsonify

from app.exceptions import (
    IntegrationAlreadyExistsException,
    IntegrationNotFoundException,
    InvalidWebhookUrlException,
    NotificationNotFoundException,
    RepoLinkAlreadyExistsException,
    RepoLinkNotFoundException,
)


def register_exception_handlers(app: Flask):
    @app.errorhandler(InvalidWebhookUrlException)
    def handle_invalid_webhook_url(error):
        response = jsonify({"error": "Invalid webhook URL"})
        response.status_code = 400
        return response

    @app.errorhandler(IntegrationAlreadyExistsException)
    def handle_integration_already_exists(error):
        response = jsonify({"error": "Integration already exists"})
        response.status_code = 409
        return response

    @app.errorhandler(IntegrationNotFoundException)
    def handle_integration_not_found(error):
        response = jsonify({"error": "Integration not found"})
        response.status_code = 404
        return response

    @app.errorhandler(RepoLinkAlreadyExistsException)
    def handle_repo_link_already_exists(error):
        response = jsonify({"error": "Repository link already exists"})
        response.status_code = 409
        return response

    @app.errorhandler(RepoLinkNotFoundException)
    def handle_repo_link_not_found(error):
        response = jsonify({"error": "Repository link not found"})
        response.status_code = 404
        return response

    @app.errorhandler(NotificationNotFoundException)
    def handle_notification_not_found(error):
        response = jsonify({"error": "Notification not found"})
        response.status_code = 404
        return response