import boto3
import logging
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

load_dotenv()


class AWSBotoClient:
    def __init__(self):
        self.secret_key = os.getenv("AWS_SECRET_KEY")
        self.access_key = os.getenv("AWS_ACCESS_KEY")
        self.bucket_name = "giltongmu"
        self.region = "ap-northeast-2"
        self.s3 = boto3.client('s3', aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key, region_name=self.region)

    def upload_file(self, folder_name: str, user_id: int, file_name: str, file_obj):
        self.s3.upload_fileobj(file_obj, self.bucket_name, f"{folder_name}/{user_id}/{file_name}")

    def get_file(self, key: str):
        try:
            link = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=3600,
            )
        except ClientError as e:
            logging.error(e)
            return None

        return link

    def delete_file(self, file_name: str):
        self.s3.delete_object(Bucket=self.bucket_name, Key=file_name)