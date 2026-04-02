"""Source acquisition exports."""

from .acquire import acquire_from_url, InvalidSourceUrlError, UnsupportedSourceError, detect_source_from_url
from .youtube import YouTubeVideoAcquirer, is_supported_youtube_watch_url
from .xiaoyuzhou import XiaoyuzhouAudioAcquirer, is_supported_xiaoyuzhou_episode_url

__all__ = [
    "acquire_from_url",
    "detect_source_from_url",
    "InvalidSourceUrlError",
    "UnsupportedSourceError",
    "YouTubeVideoAcquirer",
    "is_supported_youtube_watch_url",
    "XiaoyuzhouAudioAcquirer",
    "is_supported_xiaoyuzhou_episode_url",
]
