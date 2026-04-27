from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.models.player_stat import PlayerStat
from app.cache import get_cached_stats, set_cached_stats, clear_cache
from app.tasks.tasks import fetch_stats_task, import_all_stats_task, warmup_cache_task

router = APIRouter()


class StatsRequest(BaseModel):
    bbrefid: str
    year: int


class BatchStatsRequest(BaseModel):
    requests: List[StatsRequest]


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "bmpl-stats-api"}


@router.get("/stats/{bbrefid}/{year}")
async def get_stats(
    bbrefid: str,
    year: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Get stats for a player.

    Three-tier fallback:
    1. Check Redis cache (fast)
    2. Check database (medium)
    3. Trigger async fetch from MLB API (slow, returns empty)
    """
    # Tier 1: Check cache
    cached = get_cached_stats(bbrefid, year)
    if cached:
        return cached

    # Tier 2: Check database
    player_stat = db.query(PlayerStat).filter_by(
        bbrefid=bbrefid,
        year=year
    ).first()

    if player_stat:
        # Write to cache and return
        set_cached_stats(bbrefid, year, player_stat.stats)
        return player_stat.stats

    # Tier 3: Trigger background fetch
    background_tasks.add_task(fetch_stats_task.delay, bbrefid, year)

    return {}


@router.post("/stats/batch")
async def get_stats_batch(
    request: BatchStatsRequest,
    db: Session = Depends(get_db)
):
    """
    Batch fetch stats for multiple players.
    Returns all available stats from cache/DB.
    """
    results = []

    for req in request.requests:
        # Try cache first
        cached = get_cached_stats(req.bbrefid, req.year)
        if cached:
            results.append({
                "bbrefid": req.bbrefid,
                "year": req.year,
                "stats": cached
            })
            continue

        # Try database
        player_stat = db.query(PlayerStat).filter_by(
            bbrefid=req.bbrefid,
            year=req.year
        ).first()

        if player_stat:
            set_cached_stats(req.bbrefid, req.year, player_stat.stats)
            results.append({
                "bbrefid": req.bbrefid,
                "year": req.year,
                "stats": player_stat.stats
            })
        else:
            results.append({
                "bbrefid": req.bbrefid,
                "year": req.year,
                "stats": {}
            })

    return results


@router.post("/admin/import")
async def trigger_import(year: int, background_tasks: BackgroundTasks):
    """
    Trigger stats import for all players.
    Admin endpoint - should be authenticated in production.
    """
    background_tasks.add_task(import_all_stats_task.delay, year)

    return {
        "message": f"Stats import started for year {year}",
        "status": "queued"
    }


@router.post("/admin/warmup")
async def trigger_warmup(year: int, background_tasks: BackgroundTasks):
    """
    Trigger cache warmup from database.
    Admin endpoint - should be authenticated in production.
    """
    background_tasks.add_task(warmup_cache_task.delay, year)

    return {
        "message": f"Cache warmup started for year {year}",
        "status": "queued"
    }


@router.delete("/admin/cache")
async def clear_stats_cache():
    """
    Clear all cached stats.
    Admin endpoint - should be authenticated in production.
    """
    count = clear_cache()

    return {
        "message": f"Cleared {count} cache entries",
        "count": count
    }
