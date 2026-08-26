from functools import wraps
from uuid import UUID

import httpx
from flask import jsonify, request
from jose import JWTError, jwt

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
            return jsonify({"error": "Unauthorized"}), 401
        return f(user_id, *args, **kwargs)
    return decorated

def require_team_admin(f):
    @wraps(f)
    def decorated(user_id, *args, **kwargs):
        team_id = kwargs.get('team_id')
        response = httpx.get(
            f"{settings.DEVBOARD_WORK_URL}/api/internal/teams/{team_id}/members/{user_id}/",
            headers={"X-Service-Key": settings.INTERNAL_API_KEY}
        )
        if response.status_code != 200:
            return jsonify({"error": "Forbidden"}), 403
        role = response.json().get("role")
        if role not in ("owner", "admin"):
            return jsonify({"error": "Forbidden"}), 403
        return f(user_id, *args, **kwargs)
    return decorated