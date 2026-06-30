from flask import current_app, url_for
from media_config import MEDIA_ASSETS


def _normalize_base_url(raw_url: str) -> str:
    """Normalize external media base URL by trimming whitespace and trailing slash."""
    return (raw_url or "").strip().rstrip("/")


def media_url(path: str) -> str:
    """
    Resolve a media URL for templates.

    When MEDIA_BASE_URL is set (for example a CloudFront domain), media files are
    served from that edge URL. Otherwise, media falls back to Flask static files,
    which keeps local development and non-CDN environments working.
    """
    clean_path = (path or "").lstrip("/")
    if not clean_path:
        return ""

    media_base_url = _normalize_base_url(current_app.config.get("MEDIA_BASE_URL", ""))
    if media_base_url:
        return f"{media_base_url}/{clean_path}"

    return url_for("static", filename=clean_path)


def init_media_app(app) -> None:
    """
    Configure media helpers for the Flask application.

    Reading MEDIA_BASE_URL from environment allows seamless migration to CloudFront:
    templates keep calling media_url(path), while infrastructure can switch media
    delivery from local static serving to CDN edge delivery by changing env config.
    """
    # Pull from centralized app config so environment handling is managed in one
    # place and remains consistent across EC2, Docker, and Kubernetes.
    app.config["MEDIA_BASE_URL"] = _normalize_base_url(app.config.get("MEDIA_BASE_URL", ""))
    app.jinja_env.globals["media_url"] = media_url
    app.jinja_env.globals["MEDIA_ASSETS"] = MEDIA_ASSETS
