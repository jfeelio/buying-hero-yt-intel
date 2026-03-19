import json
import os
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'data')


def _path(filename):
    return os.path.join(DATA_DIR, filename)


def write_daily(date_str, analyzed_videos, all_video_count):
    """Write the daily JSON file."""
    daily_themes = _extract_themes(analyzed_videos)
    top_lessons = _extract_top_lessons(analyzed_videos)

    data = {
        'date': date_str,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'videos_found': all_video_count,
        'videos_analyzed': len(analyzed_videos),
        'videos': analyzed_videos,
        'daily_themes': daily_themes,
        'top_lessons': top_lessons,
    }

    with open(_path(f'{date_str}.json'), 'w') as f:
        json.dump(data, f, indent=2)

    print(f"  Wrote {_path(f'{date_str}.json')}")


def update_index(date_str):
    """Add date to the index manifest."""
    index_path = _path('index.json')
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            index = json.load(f)
    else:
        index = {'dates': []}

    if date_str not in index['dates']:
        index['dates'].insert(0, date_str)  # newest first

    index['last_updated'] = datetime.now(timezone.utc).isoformat()

    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)


def rebuild_overview(max_days=30):
    """Rebuild overview.json from recent daily files."""
    index_path = _path('index.json')
    if not os.path.exists(index_path):
        return

    with open(index_path, 'r') as f:
        index = json.load(f)

    recent_dates = index['dates'][:max_days]

    all_acquisition_lines = []
    all_dispo_lines = []
    all_lessons = []
    all_themes = []
    total_videos = 0
    channel_counts = {}

    for date_str in recent_dates:
        daily_path = _path(f'{date_str}.json')
        if not os.path.exists(daily_path):
            continue
        with open(daily_path, 'r') as f:
            day = json.load(f)

        total_videos += day.get('videos_analyzed', 0)
        all_themes.extend(
            t['theme'] if isinstance(t, dict) else t
            for t in day.get('daily_themes', [])
        )

        for vid in day.get('videos', []):
            insights = vid.get('insights', {})
            all_acquisition_lines.extend(insights.get('acquisition_one_liners', []))
            all_dispo_lines.extend(insights.get('disposition_one_liners', []))
            all_lessons.extend(insights.get('key_lessons', []))

            ch = vid.get('channel', 'Unknown')
            channel_counts[ch] = channel_counts.get(ch, 0) + 1

    overview = {
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'days_tracked': len(recent_dates),
        'total_videos_analyzed': total_videos,
        'top_acquisition_lines': _dedupe(all_acquisition_lines)[:20],
        'top_disposition_lines': _dedupe(all_dispo_lines)[:10],
        'evergreen_lessons': _dedupe(all_lessons)[:15],
        'rolling_themes': _dedupe(all_themes)[:10],
        'channel_activity': channel_counts,
    }

    with open(_path('overview.json'), 'w') as f:
        json.dump(overview, f, indent=2)

    print(f"  Rebuilt overview.json ({len(recent_dates)} days, {total_videos} videos)")


def _dedupe(items):
    seen = set()
    result = []
    for item in items:
        key = item.strip().lower()
        if key not in seen and len(item.strip()) > 10:
            seen.add(key)
            result.append(item.strip())
    return result


def _extract_themes(videos):
    themes = []
    seen = set()
    for vid in videos:
        for trend in vid.get('insights', {}).get('trends', []):
            key = trend.strip().lower()
            if key not in seen and len(trend.strip()) > 10:
                seen.add(key)
                themes.append({
                    'theme': trend.strip(),
                    'video_title': vid.get('title', ''),
                    'video_url': vid.get('url', ''),
                    'channel': vid.get('channel', ''),
                })
    return themes[:6]


def _extract_top_lessons(videos):
    lessons = []
    for vid in videos:
        lessons.extend(vid.get('insights', {}).get('key_lessons', []))
    return _dedupe(lessons)[:8]
