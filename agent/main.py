"""
Buying Hero YouTube Intelligence Agent
Runs daily via GitHub Actions to analyze real estate wholesaling videos.
"""
import os
import sys
from datetime import datetime, timezone

# Load .env if running locally
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from channel_manager import load_channels
from youtube_client import get_service, resolve_channel_id, fetch_recent_videos
from transcript_fetcher import fetch_transcript
from analyzer import analyze_video
from deduplicator import load_seen, save_seen, is_new
from data_writer import write_daily, update_index, rebuild_overview

MAX_CLAUDE_CALLS = 30  # hard cap per run


def main():
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    print(f"\n{'='*60}")
    print(f"Buying Hero YT Intel — {today}")
    print(f"{'='*60}\n")

    # Validate API keys
    if not os.environ.get('YOUTUBE_API_KEY'):
        print('[ERROR] YOUTUBE_API_KEY not set. Exiting.')
        sys.exit(1)
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print('[ERROR] ANTHROPIC_API_KEY not set. Exiting.')
        sys.exit(1)

    # Load state
    channels = load_channels()
    seen_ids = load_seen()
    print(f"Channels to check: {len(channels)}")
    print(f"Previously seen videos: {len(seen_ids)}\n")

    # Init YouTube client
    service = get_service()

    # Fetch all new videos across channels
    all_new_videos = []
    for ch in channels:
        channel_id = resolve_channel_id(service, ch)
        if not channel_id:
            print(f"  [SKIP] Could not resolve channel: {ch['name']}")
            continue

        # Update the channel's id in case it was resolved from handle
        ch['id'] = channel_id

        print(f"  Checking: {ch['name']} ({channel_id})")
        try:
            videos = fetch_recent_videos(service, channel_id, ch['name'],
                                         uploads_playlist_id=ch.get('uploads_playlist_id'))
        except Exception as e:
            if 'quotaExceeded' in str(e) or '403' in str(e):
                print(f"  [STOP] YouTube API quota exhausted. Saving partial results.")
                break
            print(f"  [WARN] Skipping {ch['name']}: {e}")
            continue
        new_videos = [
            v for v in videos
            if is_new(v['video_id'], v['published_at'], seen_ids)
        ]
        print(f"    Found {len(videos)} recent, {len(new_videos)} new")
        all_new_videos.extend(new_videos)

    print(f"\nTotal new videos to process: {len(all_new_videos)}")

    # Analyze videos with Claude
    analyzed_videos = []
    claude_calls = 0

    for video in all_new_videos:
        if claude_calls >= MAX_CLAUDE_CALLS:
            print(f"\n[INFO] Reached Claude call limit ({MAX_CLAUDE_CALLS}). Stopping analysis.")
            break

        vid_id = video['video_id']
        print(f"\n  Analyzing: {video['title'][:70]}")
        print(f"    Channel: {video['channel']} | Views: {video['view_count']:,}")

        transcript, available = fetch_transcript(vid_id)
        video['transcript_available'] = available

        if not available:
            description = video.get('description', '').strip()
            if not description or len(description) < 100:
                print(f"    [SKIP] No transcript and no useful description")
                seen_ids.add(vid_id)
                continue
            print(f"    [INFO] No transcript — analyzing description ({len(description)} chars)")
            transcript = f"[Video description only — no transcript available]\n\n{description}"
            video['content_source'] = 'description'
        else:
            video['content_source'] = 'transcript'

        insights = analyze_video(video['title'], video['channel'], transcript, call_number=claude_calls)
        claude_calls += 1

        seen_ids.add(vid_id)

        if insights is None:
            print(f"    [SKIP] Low relevance or analysis failed")
            continue

        video['insights'] = insights
        analyzed_videos.append(video)
        print(f"    [OK] Confidence: {insights.get('confidence_score', 0):.2f} | "
              f"Relevance: {insights.get('market_relevance', 'N/A')}")

    # Save results
    print(f"\n{'='*60}")
    print(f"Run Summary:")
    print(f"  Channels checked: {len(channels)}")
    print(f"  New videos found: {len(all_new_videos)}")
    print(f"  Videos analyzed: {len(analyzed_videos)}")
    print(f"  Claude API calls: {claude_calls}")

    if analyzed_videos or len(all_new_videos) > 0:
        write_daily(today, analyzed_videos, len(all_new_videos))
        update_index(today)
        rebuild_overview()
        save_seen(seen_ids)
        print(f"\n[DONE] Data written for {today}")
    else:
        print(f"\n[INFO] No new videos found. No files written.")

    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
