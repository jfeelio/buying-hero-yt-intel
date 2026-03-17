import os
import time
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig

MAX_CHARS = 80000

PROXY_USERNAME = os.environ.get('WEBSHARE_PROXY_USERNAME')
PROXY_PASSWORD = os.environ.get('WEBSHARE_PROXY_PASSWORD')


def _get_api():
    if PROXY_USERNAME and PROXY_PASSWORD:
        proxy_config = WebshareProxyConfig(
            proxy_username=PROXY_USERNAME,
            proxy_password=PROXY_PASSWORD,
        )
        return YouTubeTranscriptApi(proxy_config=proxy_config)
    return YouTubeTranscriptApi()


def fetch_transcript(video_id):
    """Fetch transcript. Falls back to any available language if English not found."""
    try:
        time.sleep(0.5)
        api = _get_api()
        fetched = api.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
        text = ' '.join(seg.text for seg in fetched)
        return _truncate(text), True
    except Exception as e:
        # Retry without language filter
        try:
            api = _get_api()
            fetched = api.fetch(video_id)
            text = ' '.join(seg.text for seg in fetched)
            return _truncate(text), True
        except Exception as e2:
            err_type = type(e2).__name__
            err_msg = str(e2)[:200] if str(e2) else f"(no message, type={err_type})"
            print(f"  [WARN] Transcript unavailable for {video_id}: {err_type}: {err_msg}")
            return None, False


def _truncate(text):
    if len(text) <= MAX_CHARS:
        return text
    first = int(MAX_CHARS * 0.75)
    last = int(MAX_CHARS * 0.25)
    return text[:first] + '\n\n[...middle truncated...]\n\n' + text[-last:]
