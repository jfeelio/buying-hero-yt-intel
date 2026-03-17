import json
import os

CHANNELS_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'data', 'channels.json')


def load_channels():
    """Return list of enabled channel dicts."""
    with open(CHANNELS_PATH, 'r') as f:
        data = json.load(f)
    return [c for c in data['channels'] if c.get('enabled', True)]


def load_all_channels():
    """Return all channels including disabled."""
    with open(CHANNELS_PATH, 'r') as f:
        data = json.load(f)
    return data['channels']
