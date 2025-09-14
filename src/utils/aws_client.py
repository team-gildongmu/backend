from http.client import responses
from io import BytesIO
import requests
import boto3
import logging
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os
import mimetypes

load_dotenv()


class AWSBotoClient:
    def __init__(self):
        self.secret_key = os.getenv("AWS_SECRET_KEY")
        self.access_key = os.getenv("AWS_ACCESS_KEY")
        self.bucket_name = os.getenv("AWS_S3_BUCKET_NAME", "giltongmu")
        self.region = os.getenv("AWS_REGION", "ap-northeast-2")
        self.s3 = boto3.client('s3', aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key, region_name=self.region)

    def upload_file_from_url(self, folder_name: str, user_id: int, file_name: str, url: str):
        response = requests.get(url)
        response.raise_for_status()

        file_obj = BytesIO(response.content)

        self.upload_file(folder_name, user_id, file_name, file_obj)

    def upload_file(self, folder_name: str, user_id: int, file_name: str, file_obj):
        content_type, _ = mimetypes.guess_type(file_name)
        content_type = content_type or "application/octet-stream"

        self.s3.upload_fileobj(
            Fileobj=file_obj,
            Bucket=self.bucket_name,
            Key=f"{folder_name}/{user_id}/{file_name}",
            ExtraArgs={"ContentType": content_type, "ContentDisposition": "inline"}
        )

    def get_file(self, key: str):
            try:
                link = self.s3.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': key,
                        'ResponseContentDisposition': 'inline'
                    },
                    ExpiresIn=3600,
                )
            except ClientError as e:
                logging.error(e)
                return None

            return link

    def delete_file(self, file_key: str):
        response = self.s3.delete_object(Bucket=self.bucket_name, Key=file_key)
        
    def delete_user_folder(self, user_id: int):
        """Delete all S3 files for a user across all folders"""
        folders = ["profile_pics", "location_pics", "stay_pics", "review_pics"]
        
        for folder in folders:
            prefix = f"{folder}/{user_id}/"
            
            try:
                # List all objects with the prefix
                response = self.s3.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
                
                if 'Contents' in response:
                    # Prepare delete request for batch deletion
                    objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                    
                    if objects_to_delete:
                        delete_response = self.s3.delete_objects(
                            Bucket=self.bucket_name,
                            Delete={'Objects': objects_to_delete}
                        )
                        logging.info(f"Deleted {len(objects_to_delete)} files from {prefix}")
                    else:
                        logging.info(f"No files found in {prefix}")
                else:
                    logging.info(f"No files found in {prefix}")
                    
            except ClientError as e:
                logging.error(f"Error deleting files from {prefix}: {e}")
                # Don't raise exception - continue with other folders