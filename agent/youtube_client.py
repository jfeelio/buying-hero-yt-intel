import os
import time
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

API_KEY = os.environ.get('YOUTUBE_API_KEY')

# Cache uploads playlist IDs to avoid repeat channels.list calls
_uploads_playlist_cache = {}


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


def _get_uploads_playlist_id(service, channel_id, uploads_playlist_id=None):
    """Get the uploads playlist ID for a channel.

    If uploads_playlist_id is pre-supplied (from channels.json), uses it for
    free (0 quota). Otherwise falls back to channels.list (1 quota unit).

    The uploads playlist ID is deterministically: 'UU' + channel_id[2:]
    but we accept an explicit value to be safe.
    """
    if uploads_playlist_id:
        return uploads_playlist_id
    if channel_id in _uploads_playlist_cache:
        return _uploads_playlist_cache[channel_id]
    # Derive it from the channel ID (UC -> UU prefix swap)
    derived = 'UU' + channel_id[2:]
    _uploads_playlist_cache[channel_id] = derived
    return derived


def fetch_recent_videos(service, channel_id, channel_name, hours_back=48,
                        uploads_playlist_id=None):
    """Fetch videos published in the last N hours for a channel.

    Uses playlistItems.list (1 quota unit) instead of search.list (100 units).
    If uploads_playlist_id is provided (from channels.json), costs only
    1 unit (playlistItems.list) + 1 unit (videos.list) = 2 units per channel.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    # Step 1: Get uploads playlist ID (0 quota if pre-supplied, else derived)
    pid = _get_uploads_playlist_id(service, channel_id, uploads_playlist_id)
    if not pid:
        return []

    videos = []
    try:
        # Step 2: Fetch most recent items from uploads playlist (1 quota unit)
        try:
            resp = service.playlistItems().list(
                part='snippet',
                playlistId=pid,
                maxResults=10
            ).execute()
        except HttpError as e:
            if e.resp.status == 404:
                # Derived UC→UU playlist ID doesn't work for this channel — look it up
                print(f"    [INFO] Playlist not found, looking up via channels.list")
                ch_resp = service.channels().list(
                    part='contentDetails',
                    id=channel_id
                ).execute()
                items = ch_resp.get('items', [])
                if not items:
                    return []
                pid = items[0]['contentDetails']['relatedPlaylists']['uploads']
                _uploads_playlist_cache[channel_id] = pid
                resp = service.playlistItems().list(
                    part='snippet',
                    playlistId=pid,
                    maxResults=10
                ).execute()
            else:
                raise

        # Filter by publish date and collect video IDs
        video_ids = []
        for item in resp.get('items', []):
            snippet = item.get('snippet', {})
            published_at = snippet.get('publishedAt', '')
            if not published_at:
                continue
            try:
                pub_dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                if pub_dt < cutoff:
                    continue  # Older than our window — playlist is date-sorted so we can stop
            except Exception:
                continue
            resource = snippet.get('resourceId', {})
            vid_id = resource.get('videoId')
            if vid_id:
                video_ids.append(vid_id)

        if not video_ids:
            return []

        # Step 3: Fetch view counts + stats for found video IDs (1 quota unit)
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
                'description': snippet.get('description', '')[:5000],
            })

    except HttpError as e:
        if e.resp.status == 403:
            print(f"  [ERROR] Quota exceeded or API key issue: {e}")
            raise
        print(f"  [WARN] Error fetching videos for {channel_name}: {e}")
        time.sleep(2)

    return videos
