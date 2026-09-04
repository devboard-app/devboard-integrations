import hashlib
import hmac
import logging

from flask import request

from app.config import settings
from app.webhooks import webhooks_bp
from app.webhooks.services import handle_github_push

logger = logging.getLogger(__name__)

def _verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(settings.GITHUB_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


@webhooks_bp.post("/github/")
def github_webhook():
    raw_body = request.get_data()
    signature = request.headers.get("X-Hub-Signature-256")

    if not _verify_signature(raw_body, signature):
        logger.warning(
            f"Rejected GitHub webhook: invalid signature "
            f"(delivery={request.headers.get('X-GitHub-Delivery')}, "
            f"event={request.headers.get('X-GitHub-Event')}, "
            f"signature_present={signature is not None})"
        )
        return {"error": "invalid signature"}, 403

    event_type = request.headers.get("X-GitHub-Event")
    if event_type != "push":
        return {"status": "ignored"}, 200
    payload = request.get_json(silent=True)
    if payload is None:
        return {"error": "invalid payload"}, 400

    handle_github_push(payload)
    return {"status": "ok"}, 200