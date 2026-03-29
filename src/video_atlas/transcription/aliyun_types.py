from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AliyunAsrConfig:
    sample_rate: int = 16000
    channels: int = 1
    api_base: str = "https://dashscope.aliyuncs.com/api/v1"
    model: str = "fun-asr"
    language_hints: list[str] = field(default_factory=list)
    diarization_enabled: bool = True
    oss_endpoint: str | None = None
    oss_bucket_name: str | None = None
    oss_access_key_id_env: str = "OSS_ACCESS_KEY_ID"
    oss_access_key_secret_env: str = "OSS_ACCESS_KEY_SECRET"
    api_key_env: str = "ALIYUN_API_KEY"
    oss_prefix: str = "audios/"
    signed_url_expires_sec: int = 3600
    poll_interval_sec: float = 2.0
    poll_timeout_sec: float = 900.0
    retain_remote_artifacts: bool = False
