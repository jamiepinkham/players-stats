"""
Stats fetcher using pybaseball and MLB Stats API.

This is the Python equivalent of the Rails StatsFetcher service,
but can now use pybaseball directly without subprocess calls!
"""
import json
import requests
from typing import Dict, Any, Optional
from pybaseball import cache, chadwick_register

# Enable pybaseball caching
cache.enable()

# MLB Stats API base URL
MLB_STATS_API = 'https://statsapi.mlb.com/api/v1'


def build_id_mapping():
    """Build MLB ID -> BBRef ID mapping from Chadwick Register"""
    register = chadwick_register()

    mapping = {}
    reverse_mapping = {}

    for _, row in register.iterrows():
        mlb_id = row.get('key_mlbam')
        bbref_id = row.get('key_bbref')

        if mlb_id and bbref_id and str(mlb_id) != 'nan' and str(bbref_id) != 'nan':
            try:
                mapping[int(mlb_id)] = bbref_id
                reverse_mapping[bbref_id] = int(mlb_id)
            except (ValueError, TypeError):
                continue

    return mapping, reverse_mapping


def fetch_mlb_batting_stats(mlb_id: int, season: int) -> Optional[Dict[str, str]]:
    """Fetch batting stats from MLB Stats API"""
    try:
        url = f'{MLB_STATS_API}/people/{mlb_id}/stats?stats=season&season={season}&group=hitting'
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        if 'stats' in data and len(data['stats']) > 0:
            splits = data['stats'][0].get('splits', [])
            if len(splits) > 0:
                stat = splits[0].get('stat', {})

                return {
                    'G': str(stat.get('gamesPlayed', '')),
                    'PA': str(stat.get('plateAppearances', '')),
                    'AB': str(stat.get('atBats', '')),
                    'H': str(stat.get('hits', '')),
                    '2B': str(stat.get('doubles', '')),
                    '3B': str(stat.get('triples', '')),
                    'HR': str(stat.get('homeRuns', '')),
                    'R': str(stat.get('runs', '')),
                    'RBI': str(stat.get('rbi', '')),
                    'SB': str(stat.get('stolenBases', '')),
                    'BB': str(stat.get('baseOnBalls', '')),
                    'SO': str(stat.get('strikeOuts', '')),
                    'BA': str(stat.get('avg', '')),
                    'OBP': str(stat.get('obp', '')),
                    'SLG': str(stat.get('slg', '')),
                    'OPS': str(stat.get('ops', ''))
                }

        return None

    except Exception as e:
        print(f"Error fetching MLB batting stats for {mlb_id}: {e}")
        return None


def fetch_mlb_pitching_stats(mlb_id: int, season: int) -> Optional[Dict[str, str]]:
    """Fetch pitching stats from MLB Stats API"""
    try:
        url = f'{MLB_STATS_API}/people/{mlb_id}/stats?stats=season&season={season}&group=pitching'
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        if 'stats' in data and len(data['stats']) > 0:
            splits = data['stats'][0].get('splits', [])
            if len(splits) > 0:
                stat = splits[0].get('stat', {})

                return {
                    'G': str(stat.get('gamesPlayed', '')),
                    'GS': str(stat.get('gamesStarted', '')),
                    'W': str(stat.get('wins', '')),
                    'L': str(stat.get('losses', '')),
                    'SV': str(stat.get('saves', '')),
                    'IP': str(stat.get('inningsPitched', '')),
                    'H': str(stat.get('hits', '')),
                    'R': str(stat.get('runs', '')),
                    'ER': str(stat.get('earnedRuns', '')),
                    'HR': str(stat.get('homeRuns', '')),
                    'BB': str(stat.get('baseOnBalls', '')),
                    'SO': str(stat.get('strikeOuts', '')),
                    'ERA': str(stat.get('era', '')),
                    'WHIP': str(stat.get('whip', ''))
                }

        return None

    except Exception as e:
        print(f"Error fetching MLB pitching stats for {mlb_id}: {e}")
        return None


def fetch_stats_for_player(bbrefid: str, year: int) -> Dict[str, Any]:
    """
    Fetch stats for a single player from MLB Stats API.

    Returns combined batting and pitching stats.
    """
    # Build ID mapping
    _, reverse_mapping = build_id_mapping()

    if bbrefid not in reverse_mapping:
        return {}

    mlb_id = reverse_mapping[bbrefid]

    # Fetch batting and pitching
    batting = fetch_mlb_batting_stats(mlb_id, year)
    pitching = fetch_mlb_pitching_stats(mlb_id, year)

    # Combine stats
    combined = {}

    if batting:
        combined.update(batting)

    if pitching:
        if batting:
            # Two-way player - only add pitching-specific fields
            pitching_only = {k: v for k, v in pitching.items()
                           if k in ['W', 'L', 'ERA', 'GS', 'SV', 'IP', 'ER', 'WHIP']}
            combined.update(pitching_only)
        else:
            combined.update(pitching)

    return combined
