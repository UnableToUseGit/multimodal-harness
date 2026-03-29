from video_atlas.transcription import extract_audio_ffmpeg, TranscriptSegment, transcript_segments_to_srt
import time
import json
import os
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path
import oss2
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from http import HTTPStatus
from dashscope.audio.asr import Transcription
from urllib import request
import dashscope

load_dotenv()

def upload_file_to_oss(local_path: Path, object_key: str) -> None:
    with open(local_path, "rb") as f:
        bucket.put_object(object_key, f)
        
def get_signed_download_url(object_key: str, expires: int = 3600) -> str:
    # expires 单位是秒
    url = bucket.sign_url("GET", object_key, expires)
    return url

input_dir = '/share/project/minghao/Proj/VideoAFS/VideoEdit/development/local/inputs'

for case_id in os.listdir(input_dir):

    # case_id = 'case_013_knowledge_history'
    case_dir = os.path.join(input_dir, case_id)
    # video_path = f'/share/project/minghao/Proj/VideoAFS/VideoEdit/development/local/inputs/{case_id}/墨西哥是如何成为一个毒品国家的.mp4'
    
    video_path = next(
        os.path.join(case_dir, f)
        for f in os.listdir(case_dir)
        if f.lower().endswith(".mp4")
    )
    
    audio_path = os.path.join(case_dir, 'audio.wav')

    sample_rate = 16000
    channels = 1

    st = time.time()
    extract_audio_ffmpeg(video_path, audio_path, sample_rate=sample_rate, channels=channels)
    print(f'sample_rate: {sample_rate}, channels: {channels}, cost time {time.time()-st}')

    # =========================
    # Config
    # =========================
    OSS_ENDPOINT = os.environ["OSS_ENDPOINT"]  # e.g. https://oss-cn-beijing.aliyuncs.com
    OSS_BUCKET_NAME = os.environ["OSS_BUCKET_NAME"]
    OSS_ACCESS_KEY_ID = os.environ["OSS_ACCESS_KEY_ID"]
    OSS_ACCESS_KEY_SECRET = os.environ["OSS_ACCESS_KEY_SECRET"]

    auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

    local_path = Path(audio_path)
    object_key = f"audios/{case_id}/audio.wav"
    upload_file_to_oss(local_path, object_key)

    signed_url = get_signed_download_url(object_key, expires=3600)
    print("Signed URL:", signed_url)


    # 以下为北京地域url，若使用新加坡地域的模型，需将url替换为：https://dashscope-intl.aliyuncs.com/api/v1
    dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    # 若没有配置环境变量，请用百炼API Key将下行替换为：dashscope.api_key = "sk-xxx"
    dashscope.api_key = os.getenv("ALIYUN_API_KEY")

    st = time.time()

    task_response = Transcription.async_call(
        model='fun-asr',
        file_urls=[signed_url],
        diarization_enabled=True,
        language_hints=['zh', 'en']  # language_hints为可选参数，用于指定待识别音频的语言代码。取值范围请参见API参考文档。
    )

    transcription_response = Transcription.wait(task=task_response.output.task_id)
    srt_file_path = Path(os.path.join(case_dir, 'subtitles.srt'))
    raw_transcription_record = Path(os.path.join(case_dir, 'raw_transcription_result.json'))

    if transcription_response.status_code == HTTPStatus.OK:
        for transcription in transcription_response.output['results']:
            if transcription['subtask_status'] == 'SUCCEEDED':
                url = transcription['transcription_url']
                result = json.loads(request.urlopen(url).read().decode('utf8'))
                            
                with open(raw_transcription_record, 'w') as file:
                    json.dump(result, file, indent=4, ensure_ascii=False)     
                        
                # posprocess this result
                transcript_segments = []
                for sentence in result['transcripts'][0]['sentences']:
                    start_time = sentence['begin_time']/1000
                    end_time = sentence['end_time']/1000
                    text = sentence['text']
                    transcript_segments.append(
                        TranscriptSegment(start=float(start_time), end=float(end_time), text=text.strip())
                    )

                srt_file_path.write_text(transcript_segments_to_srt(transcript_segments), encoding="utf-8")

                # print(json.dumps(result, indent=4,
                #                 ensure_ascii=False))
                print('transcription success!')
            else:
                print('transcription failed!')
                print(transcription)
    else:
        print('Error: ', transcription_response.output.message)
        
    print(f'cost time: {time.time() - st}')