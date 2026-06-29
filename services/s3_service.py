import os


class S3Service:
    def __init__(self):
        self.bucket = os.getenv("S3_BUCKET_NAME", "revive-thrive-assets")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.base_url = os.getenv(
            "S3_BASE_URL",
            f"https://{self.bucket}.s3.{self.region}.amazonaws.com"
        )

    def get_s3_url(self, key):
        if not key:
            return ""

        key = key.lstrip("/")
        return f"{self.base_url}/{key}"


def get_s3_url(key):
    return S3Service().get_s3_url(key)