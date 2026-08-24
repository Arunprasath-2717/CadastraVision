"""
app/jobs/worker.py
───────────────────
Background Worker processing asynchronous AI & geospatial processing tasks.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Dict
from app.jobs.queue import JobQueue, QueueJobStatus, job_queue

logger = logging.getLogger(__name__)


class BackgroundJobWorker:
    """
    Background worker consuming queue tasks.
    """

    def __init__(self, queue: JobQueue | None = None) -> None:
        self.queue = queue or job_queue
        self.handlers: Dict[str, Callable] = {}
        self._running = False

    def register_handler(self, task_type: str, handler: Callable) -> None:
        self.handlers[task_type] = handler

    async def process_one(self) -> bool:
        job = await self.queue.dequeue()
        if not job:
            return False

        handler = self.handlers.get(job.task_type)
        if not handler:
            self.queue.mark_failed(job.job_id, f"No registered handler for task_type '{job.task_type}'.")
            return True

        try:
            result = await handler(job.payload)
            self.queue.mark_completed(job.job_id, result or {"status": "ok"})
            logger.info(f"[WORKER] Successfully completed job={job.job_id} task={job.task_type}")
        except Exception as exc:
            logger.error(f"[WORKER] Error executing job={job.job_id} task={job.task_type}: {exc}")
            self.queue.mark_failed(job.job_id, str(exc))

        return True

    async def start(self) -> None:
        self._running = True
        while self._running:
            processed = await self.process_one()
            if not processed:
                await asyncio.sleep(0.1)

    def stop(self) -> None:
        self._running = False
