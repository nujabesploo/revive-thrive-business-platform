import os
import boto3

class S3Service:
    def __init__(self):
        self.bucket = os.getenv("S3_BUCKET_NAME")
        self.region = os.getenv("AWS_REGION")

        self.client = boto3.client(
            "s3",
            region_name=self.region
        )