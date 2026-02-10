"""
S3 Service for uploading graphs and files
"""

import logging
import boto3
import base64
from datetime import datetime
from typing import Optional
from botocore.exceptions import ClientError
import os

logger = logging.getLogger(__name__)


class S3Service:
    """AWS S3 file upload service"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'eu-north-1')
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET', 'water-analysis')
    
    def upload_base64_image(
        self,
        base64_data: str,
        folder: str = "graphs",
        filename: Optional[str] = None
    ) -> dict:
        """
        Upload base64 encoded image to S3
        
        Args:
            base64_data: Base64 encoded image string
            folder: S3 folder/prefix (e.g., "graphs", "reports")
            filename: Custom filename (auto-generated if not provided)
        
        Returns:
            {
                "url": "https://s3.amazonaws.com/...",
                "key": "graphs/...",
                "bucket": "water-analysis"
            }
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_graph.png"
            
            # Construct S3 key
            s3_key = f"{folder}/{filename}"
            
            # Decode base64
            image_data = base64.b64decode(base64_data)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=image_data,
                ContentType='image/png',
                ACL='public-read'  # Make publicly accessible
            )
            
            # Construct URL
            url = f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_key}"
            
            logger.info(f"✅ Uploaded to S3: {s3_key}")
            
            return {
                "url": url,
                "key": s3_key,
                "bucket": self.bucket_name,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            logger.error(f"❌ S3 upload failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ S3 upload error: {e}")
            raise
    
    def upload_file(
        self,
        file_path: str,
        folder: str = "files",
        filename: Optional[str] = None
    ) -> dict:
        """
        Upload file from local path to S3
        """
        try:
            if not filename:
                filename = os.path.basename(file_path)
            
            s3_key = f"{folder}/{filename}"
            
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ACL': 'public-read'}
            )
            
            url = f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{s3_key}"
            
            logger.info(f"✅ File uploaded to S3: {s3_key}")
            
            return {
                "url": url,
                "key": s3_key,
                "bucket": self.bucket_name
            }
            
        except Exception as e:
            logger.error(f"❌ File upload failed: {e}")
            raise
    
    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"✅ Deleted from S3: {s3_key}")
            return True
        except Exception as e:
            logger.error(f"❌ Delete failed: {e}")
            return False