import boto3
from botocore.exceptions import NoCredentialsError
import uuid
import os

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_BUCKET = os.getenv("AWS_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)

def upload_to_s3(file):
    try:
        file_extension = file.filename.split(".")[-1]
        s3_key = f"lawyers/{uuid.uuid4()}.{file_extension}"

        s3.upload_fileobj(
            file.file,
            AWS_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": file.content_type}
        )

        return f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

    except NoCredentialsError:
        raise ValueError("AWS credentials not configured properly")
 