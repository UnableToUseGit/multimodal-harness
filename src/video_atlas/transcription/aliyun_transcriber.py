from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from .aliyun_asr import AliyunAsrClient
from .aliyun_oss import AliyunOssClient
from .aliyun_types import AliyunAsrConfig
from .base import BaseTranscriber
from .types import TranscriptSegment


class AliyunAsrTranscriber(BaseTranscriber):
    def __init__(
        self,
        config: AliyunAsrConfig | dict[str, Any] | None = None,
        *,
        oss_client: AliyunOssClient | None = None,
        asr_client: AliyunAsrClient | None = None,
    ):
        if config is None:
            self.config = AliyunAsrConfig()
        elif isinstance(config, dict):
            self.config = AliyunAsrConfig(**config)
        else:
            self.config = config

        self.oss_client = oss_client or AliyunOssClient(self.config)
        self.asr_client = asr_client or AliyunAsrClient(self.config)

    def _build_object_key(self, audio_path: str | Path) -> str:
        path = Path(audio_path)
        prefix = self.config.oss_prefix.strip("/")
        if prefix:
            return f"{prefix}/{uuid4().hex}/{path.name}"
        return f"{uuid4().hex}/{path.name}"

    def transcribe_audio(self, audio_path: str | Path) -> list[TranscriptSegment]:
        path = Path(audio_path)
        object_key = self._build_object_key(path)
        self.oss_client.upload_file(path, object_key)

        try:
            signed_url = self.oss_client.get_signed_download_url(
                object_key,
                expires=self.config.signed_url_expires_sec,
            )
            return self.asr_client.transcribe_from_url(signed_url)
        finally:
            if not self.config.retain_remote_artifacts and hasattr(self.oss_client, "delete_object"):
                try:
                    self.oss_client.delete_object(object_key)
                except Exception:
                    pass
