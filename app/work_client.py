import httpx

from app.config import settings


def get_internal(path: str, timeout: float = 3.0) -> httpx.Response | None:
    try:
        return httpx.get(
            f"{settings.DEVBOARD_WORK_URL}{path}",
            headers={"X-Service-Key": settings.INTERNAL_API_KEY},
            timeout=timeout,
        )
    except httpx.TransportError:
        return None