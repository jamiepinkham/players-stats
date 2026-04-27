"""
Background tasks for stats fetching and processing.
"""
from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.player_stat import PlayerStat
from app.cache import set_cached_stats, get_cache_key
from app.services.stats_fetcher import fetch_stats_for_player
import redis
from app.config import get_settings

settings = get_settings()


@celery_app.task(name="fetch_stats")
def fetch_stats_task(bbrefid: str, year: int):
    """
    Fetch stats for a single player from MLB API.
    Creates/updates PlayerStat record and caches result.
    """
    # Fetch from MLB API
    stats = fetch_stats_for_player(bbrefid, year)

    if not stats:
        return {"status": "no_stats", "bbrefid": bbrefid, "year": year}

    # Save to database
    db = SessionLocal()
    try:
        player_stat = db.query(PlayerStat).filter_by(
            bbrefid=bbrefid,
            year=year
        ).first()

        if player_stat:
            player_stat.stats = stats
        else:
            player_stat = PlayerStat(
                bbrefid=bbrefid,
                year=year,
                stats=stats
            )
            db.add(player_stat)

        db.commit()

        # Cache the result
        set_cached_stats(bbrefid, year, stats)

        return {"status": "success", "bbrefid": bbrefid, "year": year}

    finally:
        db.close()


@celery_app.task(name="import_all_stats")
def import_all_stats_task(year: int):
    """
    Import stats for all players for a given year.
    This is the equivalent of `rake stats:import`.
    """
    # This would need a list of bbrefids to import
    # For now, placeholder - you'd query all unique bbrefids
    # from the main players database or provide a list

    return {"status": "not_implemented", "message": "Needs bbrefid list"}


@celery_app.task(name="warmup_cache")
def warmup_cache_task(year: int):
    """
    Warm up cache from database records.
    Equivalent to `rake cache:warmup`.
    """
    db = SessionLocal()
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    try:
        player_stats = db.query(PlayerStat).filter_by(year=year).all()

        cached_count = 0

        for player_stat in player_stats:
            key = get_cache_key(player_stat.bbrefid, player_stat.year)

            # Skip if already cached
            if redis_client.exists(key):
                continue

            set_cached_stats(player_stat.bbrefid, player_stat.year, player_stat.stats)
            cached_count += 1

        return {
            "status": "success",
            "year": year,
            "cached_count": cached_count,
            "total": len(player_stats)
        }

    finally:
        db.close()
