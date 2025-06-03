import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from datetime import datetime, timezone
from src.config import R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, R2_BUCKET_NAME, R2_REGION

s3_client = boto3.client(
    "s3",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    endpoint_url=R2_ENDPOINT,
    region_name=R2_REGION
)


async def upload_file_to_r2(file_data: bytes, upload_path: str) -> str:
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        file_key = f"{upload_path}/{timestamp}".strip("/")
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=file_key,
            Body=file_data,
            ContentType="image/jpeg",
        )
        return file_key

    except (NoCredentialsError, ClientError) as e:
        print(f"Error when uploading to R2: {e}")
        return None
