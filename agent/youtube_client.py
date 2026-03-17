import os
import time
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

API_KEY = os.environ.get('YOUTUBE_API_KEY')


def get_service():
    return build('youtube', 'v3', developerKey=API_KEY)


def resolve_channel_id(service, channel):
    """If channel has no id, resolve it from handle or name."""
    if channel.get('id'):
        return channel['id']
    handle = channel.get('handle', '').lstrip('@')
    if handle:
        try:
            resp = service.channels().list(
                part='id',
                forHandle=handle
            ).execute()
            items = resp.get('items', [])
            if items:
                return items[0]['id']
        except HttpError as e:
            print(f"  [WARN] Could not resolve handle @{handle}: {e}")
    return None


def fetch_recent_videos(service, channel_id, channel_name, hours_back=48):
    """Fetch videos published in the last N hours for a channel."""
    published_after = (
        datetime.now(timezone.utc) - timedelta(hours=hours_back)
    ).strftime('%Y-%m-%dT%H:%M:%SZ')

    videos = []
    try:
        resp = service.search().list(
            part='id,snippet',
            channelId=channel_id,
            publishedAfter=published_after,
            type='video',
            order='date',
            maxResults=10
        ).execute()

        video_ids = [item['id']['videoId'] for item in resp.get('items', [])]
        if not video_ids:
            return []

        # Fetch view counts + stats
        stats_resp = service.videos().list(
            part='statistics,snippet',
            id=','.join(video_ids)
        ).execute()

        for item in stats_resp.get('items', []):
            snippet = item['snippet']
            stats = item.get('statistics', {})
            videos.append({
                'video_id': item['id'],
                'title': snippet['title'],
                'channel': channel_name,
                'channel_id': channel_id,
                'published_at': snippet['publishedAt'],
                'url': f"https://youtube.com/watch?v={item['id']}",
                'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                'view_count': int(stats.get('viewCount', 0)),
                'description': snippet.get('description', '')[:500],
            })

    except HttpError as e:
        if e.resp.status == 403:
            print(f"  [ERROR] Quota exceeded or API key issue: {e}")
            raise
        print(f"  [WARN] Error fetching videos for {channel_name}: {e}")
        time.sleep(2)

    return videos
