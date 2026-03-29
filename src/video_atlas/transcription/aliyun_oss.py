from __future__ import annotations

import os
from pathlib import Path

from .aliyun_types import AliyunAsrConfig


class AliyunOssClient:
    def __init__(self, config: AliyunAsrConfig):
        self.config = config
        self._bucket = None

    def _load_bucket(self):
        if self._bucket is not None:
            return self._bucket
        if not self.config.oss_endpoint:
            raise RuntimeError("Aliyun OSS endpoint is not configured.")
        if not self.config.oss_bucket_name:
            raise RuntimeError("Aliyun OSS bucket name is not configured.")

        access_key_id = os.getenv(self.config.oss_access_key_id_env)
        access_key_secret = os.getenv(self.config.oss_access_key_secret_env)
        if not access_key_id:
            raise RuntimeError(f"Aliyun OSS access key id environment variable {self.config.oss_access_key_id_env!r} is not set.")
        if not access_key_secret:
            raise RuntimeError(f"Aliyun OSS access key secret environment variable {self.config.oss_access_key_secret_env!r} is not set.")

        try:
            import oss2
        except ImportError as exc:
            raise RuntimeError("oss2 is not installed. Install it before using AliyunAsrTranscriber.") from exc

        auth = oss2.Auth(access_key_id, access_key_secret)
        self._bucket = oss2.Bucket(auth, self.config.oss_endpoint, self.config.oss_bucket_name)
        return self._bucket

    def upload_file(self, local_path: str | Path, object_key: str) -> None:
        bucket = self._load_bucket()
        with open(local_path, "rb") as file:
            bucket.put_object(object_key, file)

    def get_signed_download_url(self, object_key: str, expires: int | None = None) -> str:
        bucket = self._load_bucket()
        return bucket.sign_url("GET", object_key, expires or self.config.signed_url_expires_sec)

    def delete_object(self, object_key: str) -> None:
        bucket = self._load_bucket()
        bucket.delete_object(object_key)
