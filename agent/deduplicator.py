import json
import os
from datetime import datetime, timezone, timedelta

SEEN_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'data', 'seen_videos.json')


def load_seen():
    if not os.path.exists(SEEN_PATH):
        return set()
    with open(SEEN_PATH, 'r') as f:
        data = json.load(f)
    return set(data.get('video_ids', []))


def save_seen(seen_ids):
    with open(SEEN_PATH, 'w') as f:
        json.dump({'video_ids': list(seen_ids)}, f)


def is_new(video_id, published_at_str, seen_ids):
    """Return True if video should be processed."""
    if video_id in seen_ids:
        return False
    # Skip anything older than 7 days regardless
    try:
        pub = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        if pub < cutoff:
            return False
    except Exception:
        pass
    return True
