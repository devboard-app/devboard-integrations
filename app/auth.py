from functools import wraps
from uuid import UUID

from flask import jsonify, request
from jose import JWTError, jwt

from app import work_client
from app.config import settings


def get_current_user_id() -> UUID | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None

def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({"detail": "Unauthorized", "errors": None}), 401
        return f(user_id, *args, **kwargs)
    return decorated

def require_team_admin(f):
    @wraps(f)
    def decorated(user_id, *args, **kwargs):
        team_id = kwargs.get('team_id')
        response = work_client.get_internal(f"/api/internal/teams/{team_id}/members/{user_id}/")
        if response is None:
            return jsonify({"detail": "Authorization service unavailable", "errors": None}), 503
        if response.status_code != 200:
            return jsonify({"detail": "Forbidden", "errors": None}), 403
        role = response.json().get("role")
        if role not in ("owner", "admin"):
            return jsonify({"detail": "Forbidden", "errors": None}), 403
        return f(user_id, *args, **kwargs)
    return decorated