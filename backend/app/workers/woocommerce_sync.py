"""Periodic, incremental WooCommerce order synchronization."""

import asyncio
import logging
from contextlib import nullcontext, suppress
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.clients.woocommerce import WooCommerceClient
from app.config import Settings
from app.database import SessionLocal
from app.importers.woocommerce_orders import import_orders

logger = logging.getLogger("uvicorn.error")
SYNC_INTERVAL_SECONDS = 30 * 60
SYNC_LOOKBACK = timedelta(hours=6)


def _acquire_lock(session: Session) -> bool:
    """Prevent duplicate work when Uvicorn or the deployment has multiple workers."""
    if session.bind is None or session.bind.dialect.name != "postgresql":
        return True
    return bool(
        session.scalar(
            text("SELECT pg_try_advisory_xact_lock(hashtext('bilen_woocommerce_orders_sync'))")
        )
    )


def sync_once(
    settings: Settings,
    *,
    now: datetime | None = None,
    session: Session | None = None,
) -> tuple[int, int] | None:
    """Upsert orders modified during the fixed rolling lookback window."""
    if not settings.woo_url or not settings.woo_key or not settings.woo_secret:
        raise ValueError("WOO_URL, WOO_KEY, and WOO_SECRET must be configured")
    started_at = now or datetime.now(UTC)
    modified_after = started_at - SYNC_LOOKBACK
    client = WooCommerceClient(settings.woo_url, settings.woo_key, settings.woo_secret)
    logger.info("WooCommerce sync starting: modified_after=%s", modified_after.isoformat())
    session_context = nullcontext(session) if session is not None else SessionLocal()
    with session_context as database_session:
        if not _acquire_lock(database_session):
            logger.info("WooCommerce sync skipped because another worker holds the lock")
            database_session.rollback()
            return None
        imported, unmatched = import_orders(
            client,
            database_session,
            modified_after=modified_after,
            commit=False,
        )
        database_session.commit()
    logger.info(
        "WooCommerce sync complete: imported=%d unmatched=%d",
        imported,
        unmatched,
    )
    return imported, unmatched


async def run_sync_loop(settings: Settings, stop: asyncio.Event) -> None:
    """Run immediately, then poll until application shutdown."""
    while not stop.is_set():
        try:
            await asyncio.to_thread(sync_once, settings)
        except Exception:
            logger.exception("WooCommerce order sync failed; it will retry")
        with suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=SYNC_INTERVAL_SECONDS)
