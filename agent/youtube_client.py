import os
import time
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

API_KEY = os.environ.get('YOUTUBE_API_KEY')


def get_service():
    return build('youtube', 'v3', developerKey=API_KEY)


def resolve_channel_id(service, channel):
    if channel.get('id'):
        return channel['id']
    handle = channel.get('handle', '').lstrip('@')
    if handle:
        try:
            resp = service.channels().list(part='id', forHandle=handle).execute()
            items = resp.get('items', [])
            if items:
                return items[0]['id']
        except HttpError as e:
            if e.resp.status == 403:
                print(f"  [QUOTA] YouTube API quota exceeded during channel resolution.")
                raise
            print(f"  [WARN] Could not resolve handle @{handle}: {e}")
    return None


def _get_uploads_playlist_id(channel_id):
    """Convert channel ID to uploads playlist ID: UCxxxx -> UUxxxx"""
    if channel_id.startswith('UC'):
        return 'UU' + channel_id[2:]
    return None


def fetch_recent_videos(service, channel_id, channel_name, hours_back=48):
    """Fetch recent videos using playlistItems.list (1 quota unit vs 100 for search.list)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    uploads_playlist = _get_uploads_playlist_id(channel_id)

    if not uploads_playlist:
        return []

    videos = []
    try:
        # playlistItems.list costs 1 unit (vs search.list at 100 units)
        resp = service.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist,
            maxResults=10
        ).execute()

        recent_items = []
        for item in resp.get('items', []):
            snippet = item['snippet']
            published = snippet.get('publishedAt', '')
            try:
                pub_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                if pub_dt >= cutoff:
                    video_id = snippet.get('resourceId', {}).get('videoId')
                    if video_id:
                        recent_items.append({
                            'video_id': video_id,
                            'published_at': published,
                            'title': snippet.get('title', ''),
                            'description': snippet.get('description', '')[:5000],
                        })
            except Exception:
                pass

        if not recent_items:
            return []

        # Get statistics via videos.list (1 unit)
        video_ids = [v['video_id'] for v in recent_items]
        stats_resp = service.videos().list(
            part='statistics,snippet',
            id=','.join(video_ids)
        ).execute()

        stats_map = {}
        for item in stats_resp.get('items', []):
            snippet = item['snippet']
            stats = item.get('statistics', {})
            stats_map[item['id']] = {
                'view_count': int(stats.get('viewCount', 0)),
                'description': snippet.get('description', '')[:5000],
                'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                'title': snippet.get('title', ''),
            }

        for v in recent_items:
            vid_id = v['video_id']
            s = stats_map.get(vid_id, {})
            videos.append({
                'video_id': vid_id,
                'title': s.get('title', v['title']),
                'channel': channel_name,
                'channel_id': channel_id,
                'published_at': v['published_at'],
                'url': f"https://youtube.com/watch?v={vid_id}",
                'thumbnail': s.get('thumbnail', ''),
                'view_count': s.get('view_count', 0),
                'description': s.get('description', v.get('description', '')),
            })

    except HttpError as e:
        if e.resp.status == 403:
            print(f"  [QUOTA] YouTube API quota exceeded for {channel_name}. Stopping channel scan.")
            raise
        print(f"  [WARN] Error fetching videos for {channel_name}: {e}")
        time.sleep(2)

    return videos
