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
from app.models import IntegrationSyncState

logger = logging.getLogger(__name__)
SYNC_NAME = "woocommerce_orders"
SYNC_OVERLAP = timedelta(minutes=5)
SYNC_INTERVAL_SECONDS = 300
INITIAL_LOOKBACK = timedelta(hours=24)


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


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
    """Fetch orders modified since the persistent cursor and commit them atomically."""
    if not settings.woo_url or not settings.woo_key or not settings.woo_secret:
        raise ValueError("WOO_URL, WOO_KEY, and WOO_SECRET must be configured")
    started_at = now or datetime.now(UTC)
    client = WooCommerceClient(settings.woo_url, settings.woo_key, settings.woo_secret)
    session_context = nullcontext(session) if session is not None else SessionLocal()
    with session_context as database_session:
        if not _acquire_lock(database_session):
            logger.info("WooCommerce sync skipped because another worker holds the lock")
            database_session.rollback()
            return None
        state = database_session.get(IntegrationSyncState, SYNC_NAME)
        if state is None:
            state = IntegrationSyncState(name=SYNC_NAME)
            database_session.add(state)
        state.last_started_at = started_at
        modified_after = (
            _utc(state.cursor_at) - SYNC_OVERLAP
            if state.cursor_at
            else started_at - INITIAL_LOOKBACK
        )
        imported, unmatched = import_orders(
            client,
            database_session,
            modified_after=modified_after,
            commit=False,
        )
        state.cursor_at = started_at
        state.last_completed_at = datetime.now(UTC)
        state.last_imported = imported
        state.last_unmatched = unmatched
        database_session.commit()
    logger.info("WooCommerce sync complete: %d orders, %d unmatched items", imported, unmatched)
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
