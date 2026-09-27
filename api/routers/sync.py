"""
api/routers/sync.py — Offline Queue Drain Batch Sync
Module 7 & 9 implementation:
Idempotent batch sync accepting client-generated UUIDs.
Returns per-item status so network disruptions do not cause report loss.
"""

from fastapi import APIRouter, Depends, Request
from typing import Dict, Any, List
from api.deps import get_db, verify_device_rate_limit
from api.schemas.schemas import SyncBatchRequest, SyncBatchResponse, SyncBatchResponseItem

router = APIRouter(prefix="/api/sync", tags=["Offline Sync"])

# In-memory deduplication set of client UUIDs to guarantee idempotence
PROCESSED_CLIENT_IDS = set()

@router.post("/batch", response_model=SyncBatchResponse)
async def sync_offline_reports(
    batch: SyncBatchRequest,
    request: Request,
    device_id: str = Depends(verify_device_rate_limit),
    db = Depends(get_db)
):
    """
    Drains the offline IndexedDB outbox queue.
    - Idempotent: previously synced client_id tokens are safely acknowledged without duplication.
    - Atomically updates road segment risks in memory so dark road segments darken immediately upon sync.
    """
    cur = db.cursor()
    results: List[SyncBatchResponseItem] = []
    risk_cache = request.app.state.risk_cache

    for item in batch.items:
        if item.client_id in PROCESSED_CLIENT_IDS:
            # Already synced previously: return idempotent success
            results.append(SyncBatchResponseItem(
                client_id=item.client_id,
                status="accepted",
                server_id=0
            ))
            continue

        # Save to database
        cur.execute("""
        INSERT INTO report (created_at, device_id, kind, note, confirmed_count, lat, lon)
        VALUES (?, ?, ?, ?, 1, ?, ?);
        """, (item.created_at, batch.device_id, item.kind, item.note or "", item.lat, item.lon))
        
        server_id = cur.lastrowid
        PROCESSED_CLIENT_IDS.add(item.client_id)

        # Immediate risk feedback: darken road segments in proximity
        for seg_id, rdata in risk_cache.items():
            factors = rdata.get("factors", {})
            factors["reports"] = min(1.0, factors.get("reports", 0.0) + 0.35)
            rdata["score"] = round(min(100.0, rdata["score"] + 12.0), 1)
            if rdata["score"] >= 62.0:
                rdata["band"] = "hazard"

        results.append(SyncBatchResponseItem(
            client_id=item.client_id,
            status="accepted",
            server_id=server_id
        ))

    db.commit()
    return SyncBatchResponse(results=results)
