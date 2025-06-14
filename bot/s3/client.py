from aioboto3 import Session
from botocore.config import Config

from bot.config import S3_CONFIG


_session : Session = Session()

cfg : Config = Config(
    signature_version="s3v4",
)

def get_client():
    return _session.client(
        "s3",
        endpoint_url=S3_CONFIG.ENDPOINT_URL,
        aws_access_key_id=S3_CONFIG.ACCESS_KEY,
        aws_secret_access_key=S3_CONFIG.SECRET_KEY,
        region_name=S3_CONFIG.REGION,
        config=cfg
    )   