import os
import secrets


class Config:
    """Application configuration loaded from environment variables.

    Keeping configuration in one place makes runtime behavior predictable across
    local development, EC2 systemd deployments, Docker images, and Kubernetes.
    """

    SECRET_KEY = secrets.token_hex(32)
    MEDIA_BASE_URL = ""
    S3_BASE_URL = ""

    @staticmethod
    def init_app(app) -> None:
        """Load environment-driven settings after dotenv is initialized."""
        app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", Config.SECRET_KEY)
        production = os.getenv("APP_ENV") == "production"
        if production and not os.getenv("FLASK_SECRET_KEY"):
            raise RuntimeError("Production requires a persistent FLASK_SECRET_KEY.")
        app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=production)

        hero_path = os.getenv("HERO_IMAGE_PATH", "hero/repair-cinematic-v1.png").strip()
        if hero_path.startswith('/') or '..' in hero_path.split('/') or ':' in hero_path:
            raise RuntimeError("HERO_IMAGE_PATH must be a relative static asset path.")
        app.config["HERO_IMAGE_PATH"] = hero_path

        # Media delivery base URL (CloudFront in production). When empty, the app
        # falls back to Flask static file URLs for local/non-CDN environments.
        app.config["MEDIA_BASE_URL"] = os.getenv("MEDIA_BASE_URL", "").strip().rstrip("/")

        # Backward-compatible variable retained for transition visibility.
        app.config["S3_BASE_URL"] = os.getenv("S3_BASE_URL", "").strip().rstrip("/")
