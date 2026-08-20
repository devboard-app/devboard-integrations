from functools import wraps
from uuid import UUID

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