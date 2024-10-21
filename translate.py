import httpx
import os
from dotenv import load_dotenv
import json
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import backoff  # 你需要安装这个库：pip install backoff

from prompt import to_zh, whether_to_trans_prompt

# 加载环境变量中的 API 密钥
load_dotenv()
OPENAI_APIKEY = os.getenv('OPENAI_APIKEY')

# 创建一个线程本地存储对象
thread_local = threading.local()

# 创建一个简单的速率限制器类
class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = threading.Lock()

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                # 移除过期的调用记录
                self.calls = [call for call in self.calls if now - call < self.period]
                if len(self.calls) >= self.max_calls:
                    sleep_time = self.period - (now - self.calls[0])
                    time.sleep(sleep_time)
                self.calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper

# 修改速率限制器实例，适应 tier1 用户的限制
rate_limiter = RateLimiter(max_calls=450, period=60)  # 每分钟450个请求，略低于500 RPM 限制

# 添加每日请求计数器
daily_request_count = 0
daily_request_lock = threading.Lock()

def increment_daily_count():
    global daily_request_count
    with daily_request_lock:
        daily_request_count += 1
        return daily_request_count

# 获取或创建线程本地的 httpx.Client 对象
def get_httpx_client():
    if not hasattr(thread_local, "client"):
        thread_local.client = httpx.Client()
    return thread_local.client

# 修改 translate 函数为多线程版本
def translate(text, platform, target_language='简体中文'):
    match platform:
        case "openai":
            translations = openai_trans(to_zh.format(text), target_language)
        case _:
            raise ValueError(f"不支持的平台: {platform}")

    return translations

def whether_to_trans(text, platform):
    match platform:
        case "openai":
            flag = openai_trans(whether_to_trans_prompt.format(text))
            # 确保返回值是 "True" 或 "False"
            if flag is not None:
                flag = "True" if flag.strip().lower() in ['true', '1', 'yes'] else "False"
        case _:
            raise ValueError(f"不支持的平台: {platform}")

    return flag

# 多线程翻译函数，使用 OpenAI 的接口通过 httpx 请求
@backoff.on_exception(backoff.expo,
                      (httpx.HTTPError, ValueError),
                      max_tries=5,
                      max_time=300)
@rate_limiter
def openai_trans(text, target_language='简体中文', model="gpt-4o-mini"):
    global daily_request_count
    if increment_daily_count() > 9900:  # 设置一个略低于限制的阈值
        print("达到每日请求限制，请等待重置")
        return None

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_APIKEY}"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一位精通简体中文的专业翻译。"
            },
            {"role": "user", "content": text}
        ]
    }

    client = get_httpx_client()
    response = client.post(url, headers=headers, json=payload)
    response.raise_for_status()  # 这会在状态码不是 2xx 时抛出异常
    result = response.json()
    return result['choices'][0]['message']['content']

# 创建线程池
executor = ThreadPoolExecutor(max_workers=10)  # 可以根据需要调整线程数

# 多线程翻译函数
def translate_multi(texts, platform, target_language='简体中文'):
    futures = [executor.submit(translate, text, platform, target_language) for text in texts]
    return [future.result() for future in futures]

# 多线程翻译函数
def whether_to_trans_multi(texts, platform):
    futures = [executor.submit(whether_to_trans, text, platform) for text in texts]
    return [future.result() for future in futures]
