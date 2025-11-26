# app/core/background_tasks.py
"""
Background tasks for periodic maintenance and cleanup.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import Session

from app.database.engine import get_db
from app.services.notification_service import NotificationService
from app.core.sse_manager import get_sse_manager

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Manages periodic background tasks."""

    def __init__(self):
        self.tasks: list[asyncio.Task] = []
        self._running = False

    async def start(self):
        """Start all background tasks."""
        if self._running:
            logger.warning("Background tasks already running")
            return

        self._running = True
        logger.info("Starting background tasks...")

        # Start periodic cleanup tasks
        self.tasks.append(asyncio.create_task(self.cleanup_expired_notifications_task()))
        self.tasks.append(asyncio.create_task(self.cleanup_stale_sse_connections_task()))
        self.tasks.append(asyncio.create_task(self.update_leaderboards_task()))

        # Newsletter campaign tasks
        self.tasks.append(asyncio.create_task(self.process_scheduled_campaigns_task()))
        self.tasks.append(asyncio.create_task(self.send_campaign_emails_task()))

        logger.info(f"Started {len(self.tasks)} background tasks")

    async def stop(self):
        """Stop all background tasks."""
        if not self._running:
            return

        logger.info("Stopping background tasks...")
        self._running = False

        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.tasks.clear()
        logger.info("Background tasks stopped")

    async def cleanup_expired_notifications_task(self):
        """
        Periodically clean up expired notifications.
        Runs every hour.
        """
        while self._running:
            try:
                await asyncio.sleep(3600)  # Run every hour

                # Get a database session
                db_gen = get_db()
                db = next(db_gen)

                try:
                    count = NotificationService.cleanup_expired_notifications(db)
                    if count > 0:
                        logger.info(f"Cleaned up {count} expired notifications")
                finally:
                    # Close the database session
                    try:
                        next(db_gen)
                    except StopIteration:
                        pass

            except asyncio.CancelledError:
                logger.info("Expired notifications cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in expired notifications cleanup task: {e}")
                # Wait before retrying
                await asyncio.sleep(60)

    async def cleanup_stale_sse_connections_task(self):
        """
        Periodically clean up stale SSE connections.
        Runs every 5 minutes.
        """
        while self._running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                sse_manager = get_sse_manager()
                count = await sse_manager.cleanup_stale_connections(timeout_seconds=300)

                if count > 0:
                    logger.info(f"Cleaned up {count} stale SSE connections")

            except asyncio.CancelledError:
                logger.info("Stale SSE connections cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in stale SSE connections cleanup task: {e}")
                # Wait before retrying
                await asyncio.sleep(60)

    async def update_leaderboards_task(self):
        """
        Periodically update all leaderboards (points, hours, projects).
        Runs every hour.
        """
        while self._running:
            try:
                await asyncio.sleep(3600)  # Run every hour

                # Get a database session
                db_gen = get_db()
                db = next(db_gen)

                try:
                    from app.services.gamification_service import GamificationService

                    count = GamificationService.update_all_leaderboards(db)
                    logger.info(f"Updated {count} leaderboards")
                finally:
                    # Close the database session
                    try:
                        next(db_gen)
                    except StopIteration:
                        pass

            except asyncio.CancelledError:
                logger.info("Leaderboard update task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in leaderboard update task: {e}")
                # Wait before retrying
                await asyncio.sleep(60)

    async def process_scheduled_campaigns_task(self):
        """
        Check for campaigns due to be sent and start sending.
        Runs every minute.
        """
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute

                # Get a database session
                db_gen = get_db()
                db = next(db_gen)

                try:
                    from app.services.campaign_service import campaign_service

                    # Get campaigns due to be sent
                    due_campaigns = campaign_service.get_due_campaigns(db)

                    for campaign in due_campaigns:
                        # Start sending the campaign
                        await campaign_service.send_campaign_now(db, campaign.id)
                        logger.info(f"Started sending scheduled campaign {campaign.id}: {campaign.name}")
                finally:
                    try:
                        next(db_gen)
                    except StopIteration:
                        pass

            except asyncio.CancelledError:
                logger.info("Scheduled campaigns task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduled campaigns task: {e}")
                await asyncio.sleep(60)

    async def send_campaign_emails_task(self):
        """
        Process pending campaign recipients in batches.
        Runs every 10 seconds when campaigns are sending.
        """
        while self._running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds

                # Get a database session
                db_gen = get_db()
                db = next(db_gen)

                try:
                    from app.services.campaign_service import campaign_service
                    from app.core.config import settings

                    # Get campaigns that are currently sending
                    sending_campaigns = campaign_service.get_sending_campaigns(db)

                    for campaign in sending_campaigns:
                        # Process a batch of emails
                        sent, remaining = await campaign_service.process_campaign_batch(
                            db,
                            campaign.id,
                            batch_size=settings.CAMPAIGN_BATCH_SIZE,
                            delay_seconds=settings.CAMPAIGN_BATCH_DELAY_SECONDS
                        )

                        if sent > 0:
                            logger.info(f"Campaign {campaign.id}: sent {sent} emails, {remaining} remaining")

                        if remaining == 0:
                            logger.info(f"Campaign {campaign.id} sending complete")
                finally:
                    try:
                        next(db_gen)
                    except StopIteration:
                        pass

            except asyncio.CancelledError:
                logger.info("Campaign sending task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in campaign sending task: {e}")
                await asyncio.sleep(30)


# Global background task manager instance
background_task_manager: Optional[BackgroundTaskManager] = None


def get_background_task_manager() -> BackgroundTaskManager:
    """Get the global background task manager instance."""
    if background_task_manager is None:
        raise RuntimeError("BackgroundTaskManager not initialized")
    return background_task_manager
