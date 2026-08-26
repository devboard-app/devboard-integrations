from uuid import UUID

from flask import abort, jsonify, request

from app.auth import jwt_required, require_team_admin
from app.integrations import integrations_bp
from app.integrations.services import (
    create_integration,
    create_repo_link,
    delete_repo_link,
    update_integration,
)
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


@integrations_bp.post("/<uuid:team_id>/repo-links/")
@jwt_required
@require_team_admin
def create_repo_link_view(user_id: UUID, team_id: UUID):
    data = request.get_json() or {}
    project_id = data.get("project_id")
    github_repo = data.get("github_repo")
    if not project_id or not github_repo:
        return jsonify({"error": "project_id and github_repo are required"}), 400
    try:
        link = create_repo_link(team_id, UUID(project_id), github_repo)
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    return jsonify({
        "id": str(link.id),
        "team_id": str(link.team_id),
        "project_id": str(link.project_id),
        "github_repo": link.github_repo,
    }), 201

@integrations_bp.delete("/<uuid:team_id>/repo-links/<uuid:repo_link_id>/")
@jwt_required
@require_team_admin
def delete_repo_link_view(user_id: UUID, team_id: UUID, repo_link_id: UUID):
    try:
        delete_repo_link(team_id, repo_link_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    return "", 204