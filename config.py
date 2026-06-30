import os


class Config:
    """Application configuration loaded from environment variables.

    Keeping configuration in one place makes runtime behavior predictable across
    local development, EC2 systemd deployments, Docker images, and Kubernetes.
    """

    SECRET_KEY = "revive-thrive-secret"
    MEDIA_BASE_URL = ""
    S3_BASE_URL = ""

    @staticmethod
    def init_app(app) -> None:
        """Load environment-driven settings after dotenv is initialized."""
        app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", Config.SECRET_KEY)

        # Media delivery base URL (CloudFront in production). When empty, the app
        # falls back to Flask static file URLs for local/non-CDN environments.
        app.config["MEDIA_BASE_URL"] = os.getenv("MEDIA_BASE_URL", "").strip().rstrip("/")

        # Backward-compatible variable retained for transition visibility.
        app.config["S3_BASE_URL"] = os.getenv("S3_BASE_URL", "").strip().rstrip("/")
