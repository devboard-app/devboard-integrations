from uuid import UUID

from flask import jsonify, request

from app.auth import jwt_required, require_team_admin
from app.integrations import integrations_bp
from app.integrations.services import (
    create_integration,
    create_repo_link,
    delete_repo_link,
    get_integration_or_404,
    update_integration,
)


@integrations_bp.get("/<uuid:team_id>/")
@jwt_required
@require_team_admin
def get_integration_view(user_id: UUID, team_id: UUID):
    integration = get_integration_or_404(team_id)
    return jsonify(integration.to_dict()), 200

@integrations_bp.post("/<uuid:team_id>/")
@jwt_required
@require_team_admin
def create_integration_view(user_id: UUID, team_id: UUID):
    data = request.get_json() or {}
    integration = create_integration(team_id, data)
    return jsonify(integration.to_dict()), 201

@integrations_bp.patch("/<uuid:team_id>/")
@jwt_required
@require_team_admin
def update_integration_view(user_id: UUID, team_id: UUID):
    data = request.get_json() or {}
    integration = update_integration(team_id, data)
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
        project_uuid = UUID(project_id)
    except ValueError:
        return jsonify({"error": "project_id must be a valid UUID"}), 400

    link = create_repo_link(team_id, project_uuid, github_repo)
    
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
    delete_repo_link(team_id, repo_link_id)
    return "", 204