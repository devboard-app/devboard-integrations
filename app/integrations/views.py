from uuid import UUID

from flask import abort, jsonify, request

from app.auth import jwt_required, require_team_admin
from app.integrations import integrations_bp
from app.integrations.services import create_integration, update_integration
from app.integrations.services import get_integration as get_integration_service


@integrations_bp.get("/<uuid:team_id>/")
@jwt_required
@require_team_admin
def get_integration(user_id: UUID, team_id: UUID):
    integration = get_integration_service(team_id)
    if integration is None:
        abort(404)
    return jsonify(integration.to_dict()), 200

@integrations_bp.post("/<uuid:team_id>/")
@jwt_required
@require_team_admin
def create_integration_view(user_id: UUID, team_id: UUID):
    data = request.get_json() or {}
    try:
        integration = create_integration(team_id, data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    return jsonify(integration.to_dict()), 201

@integrations_bp.patch("/<uuid:team_id>/")
@jwt_required
@require_team_admin
def update_integration_view(user_id: UUID, team_id: UUID):
    data = request.get_json() or {}
    try:
        integration = update_integration(team_id, data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    return jsonify(integration.to_dict()), 200
    