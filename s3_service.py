import boto3
import settings

from constants.config import S3_FILE_URL_PATH
from constants.enums import S3BucketACLPermissions
from exceptions import FileIsEmpty, FileNotFound


class S3Service:
    def __init__(self):
        self.client = self.get_s3_client()
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    @staticmethod
    def get_s3_client():
        client = boto3.client(
            "s3",
            region_name=settings.AWS_DEFAULT_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        return client

    @property
    def s3_resource(self):
        client = boto3.resource("s3", region_name=settings.AWS_DEFAULT_REGION)
        return client

    def get_object(self, key: str):
        bucket_name = self.bucket_name
        try:
            response = self.client.get_object(Bucket=bucket_name, Key=key)
        except self.client.exceptions.NoSuchKey:
            raise FileNotFound()
        streaming_body = response.get("Body")
        if streaming_body:
            return streaming_body.read()
        raise FileIsEmpty()

    def put_object(
        self,
        body: str,
        file_name: str,
        acl: str = S3BucketACLPermissions.PRIVATE.value,
    ):
        bucket_name = self.bucket_name
        print("bucket_name: ", bucket_name)
        print("file_name: ", file_name)
        self.client.put_object(
            Body=body, Bucket=bucket_name, Key=file_name, ACL=acl
        )

        s3_file_url = S3_FILE_URL_PATH % (
            settings.AWS_DEFAULT_REGION,
            bucket_name,
            file_name,
        )
        print("s3 url: ", s3_file_url)
        return s3_file_url

    def get_files_names(self, prefix: str):
        bucket_name = self.bucket_name
        response = self.client.list_objects(Bucket=bucket_name, Prefix=prefix)
        file_names = []
        for obj in response.get('Contents', []):
            file_name = obj['Key'].split('/')[-1]  # Extract the file name from the object key
            file_names.append(file_name)
        return file_names

    def delete_object(self, file_name: str):
        bucket_name = self.bucket_name
        try:
            self.client.delete_object(Bucket=bucket_name, Key=file_name)
        except self.client.exceptions.NoSuchKey:
            pass
