"""
app/jobs/queue.py
──────────────────
Async In-Memory & Distributed Job Queue for non-blocking background processing.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class QueueJobStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class QueueJob:
    job_id: str
    task_type: str
    payload: Dict[str, Any]
    status: QueueJobStatus = QueueJobStatus.QUEUED
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class JobQueue:
    """
    Async Job Queue with idempotency duplicate prevention.
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, QueueJob] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    async def enqueue(self, job_id: str, task_type: str, payload: Dict[str, Any], max_retries: int = 3) -> QueueJob:
        if job_id in self._jobs and self._jobs[job_id].status in (QueueJobStatus.QUEUED, QueueJobStatus.PROCESSING):
            # Duplicate job prevention
            return self._jobs[job_id]

        job = QueueJob(
            job_id=job_id,
            task_type=task_type,
            payload=payload,
            status=QueueJobStatus.QUEUED,
            max_retries=max_retries,
        )
        self._jobs[job_id] = job
        await self._queue.put(job_id)
        return job

    async def dequeue(self) -> Optional[QueueJob]:
        try:
            job_id = await asyncio.wait_for(self._queue.get(), timeout=0.1)
            job = self._jobs.get(job_id)
            if job:
                job.status = QueueJobStatus.PROCESSING
            return job
        except asyncio.TimeoutError:
            return None

    def get_job(self, job_id: str) -> Optional[QueueJob]:
        return self._jobs.get(job_id)

    def mark_completed(self, job_id: str, result: Dict[str, Any]) -> None:
        if job_id in self._jobs:
            self._jobs[job_id].status = QueueJobStatus.COMPLETED
            self._jobs[job_id].result = result

    def mark_failed(self, job_id: str, error: str) -> None:
        if job_id in self._jobs:
            job = self._jobs[job_id]
            job.error_message = error
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = QueueJobStatus.QUEUED
                self._queue.put_nowait(job_id)
            else:
                job.status = QueueJobStatus.FAILED


# Global job queue instance
job_queue = JobQueue()
