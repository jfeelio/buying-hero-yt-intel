import time
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

MAX_CHARS = 80000


def fetch_transcript(video_id):
    """
    Fetch transcript for a video. Returns (text, available) tuple.
    Uses 60/20 heuristic for long transcripts.
    """
    try:
        time.sleep(1)  # polite rate limiting
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=['en', 'en-US', 'en-GB']
        )
        text = ' '.join(seg['text'] for seg in transcript_list)
        text = _truncate(text)
        return text, True

    except (TranscriptsDisabled, NoTranscriptFound):
        return None, False
    except Exception as e:
        print(f"  [WARN] Transcript error for {video_id}: {e}")
        return None, False


def _truncate(text):
    """Apply 60/20 heuristic: first 60% + last 20% of content."""
    if len(text) <= MAX_CHARS:
        return text
    first = int(MAX_CHARS * 0.75)
    last = int(MAX_CHARS * 0.25)
    return text[:first] + '\n\n[...middle truncated...]\n\n' + text[-last:]
