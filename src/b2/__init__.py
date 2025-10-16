from functools import lru_cache

from src.config import Config

import b2sdk.v2 as b2

# couldn't use AWS S3 for some reason, so using Backblaze B2
@lru_cache
def b2_api():
    info = b2.InMemoryAccountInfo()
    b2_api = b2.B2Api(info)

    b2_api.authorize_account("production", Config.B2_KEY_ID, Config.B2_APPLICATION_KEY)
    return b2_api

@lru_cache
def get_b2_bucket(api: b2.B2Api):
    return api.get_bucket_by_name(Config.B2_BUCKET_NAME)

def b2_upload_file(local_file: str, filename: str) -> str:
    api = b2_api()
    bucket = get_b2_bucket(api)

    uploaded_file = bucket.upload_local_file(local_file=local_file, file_name=filename)
    
    bucket_name = bucket.name
    file_id = uploaded_file.id_
    download_url = f"https://api.backblazeb2.com/b2api/v2/b2_download_file_by_id?fileId={file_id}"

    return download_url
