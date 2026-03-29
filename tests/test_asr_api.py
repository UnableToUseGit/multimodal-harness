from http import HTTPStatus
from dashscope.audio.asr import Transcription
from urllib import request
import dashscope
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

# 以下为北京地域url，若使用新加坡地域的模型，需将url替换为：https://dashscope-intl.aliyuncs.com/api/v1
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

# 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
# 若没有配置环境变量，请用百炼API Key将下行替换为：dashscope.api_key = "sk-xxx"
dashscope.api_key = os.getenv("ALIYUN_API_KEY")

st = time.time()

url = "https://qmh-video-store.oss-cn-beijing.aliyuncs.com/audios%2Fcase_008_knowledge_history%2Faudio.wav?OSSAccessKeyId=LTAI5tMtRMR5Huijonwcqp7Y&Expires=1774786237&Signature=UCcr4UOcXGNuVRcEEiJEjjAXaFQ%3D"

task_response = Transcription.async_call(
    model='fun-asr',
    file_urls=[url],
    language_hints=['zh', 'en']  # language_hints为可选参数，用于指定待识别音频的语言代码。取值范围请参见API参考文档。
)

transcription_response = Transcription.wait(task=task_response.output.task_id)

if transcription_response.status_code == HTTPStatus.OK:
    for transcription in transcription_response.output['results']:
        if transcription['subtask_status'] == 'SUCCEEDED':
            url = transcription['transcription_url']
            result = json.loads(request.urlopen(url).read().decode('utf8'))
            with open('./result.json', 'w') as file:
                json.dump(result, file, indent=4, ensure_ascii=False)          
            # print(json.dumps(result, indent=4,
            #                 ensure_ascii=False))
            print('transcription success!')
        else:
            print('transcription failed!')
            print(transcription)
else:
    print('Error: ', transcription_response.output.message)
    
print(f'cost time: {time.time() - st}')