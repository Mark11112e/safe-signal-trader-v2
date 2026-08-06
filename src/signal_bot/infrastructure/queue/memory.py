"""
In-memory Job Queue with Claim / Lease / Heartbeat / Recovery.

Mirrors the PostgreSQL SKIP LOCKED design (ADR-0002) for unit tests
and Phase-4 development without requiring a live DB.
Production path will use OrderJobORM + SELECT FOR UPDATE SKIP LOCKED.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from signal_bot.domain.enums import JobStatus
from signal_bot.domain.models import OrderJob


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryJobQueue:
    """
    Thread-unsafe single-process queue – sufficient for unit tests.
    Semantics:
      - enqueue → PENDING
      - claim(owner, lease_s) → CLAIMED with lease_until (SKIP LOCKED style: first free)
      - heartbeat → extend lease
      - complete / fail / manual_review
      - recover_expired → release leases past deadline back to PENDING
    """

    def __init__(self) -> None:
        self._jobs: dict[UUID, OrderJob] = {}

    def enqueue(
        self,
        *,
        trade_id: UUID,
        job_type: str,
        payload: dict[str, Any] | None = None,
        client_order_id: str | None = None,
        max_attempts: int = 5,
    ) -> OrderJob:
        # Idempotency: same client_order_id → return existing
        if client_order_id:
            for j in self._jobs.values():
                if j.client_order_id == client_order_id:
                    return j
        job = OrderJob(
            trade_id=trade_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            payload=payload or {},
            client_order_id=client_order_id,
            max_attempts=max_attempts,
        )
        self._jobs[job.job_id] = job
        return job

    def claim(self, owner: str, lease_seconds: int = 30) -> OrderJob | None:
        now = _utcnow()
        for job in self._jobs.values():
            if job.status == JobStatus.PENDING or (
                job.status == JobStatus.CLAIMED
                and job.lease_until is not None
                and job.lease_until < now
            ):
                job.status = JobStatus.CLAIMED
                job.lease_owner = owner
                job.lease_until = now + timedelta(seconds=lease_seconds)
                job.attempt += 1
                job.updated_at = now
                return job
        return None

    def heartbeat(self, job_id: UUID, owner: str, lease_seconds: int = 30) -> bool:
        job = self._jobs.get(job_id)
        if not job or job.lease_owner != owner or job.status != JobStatus.CLAIMED:
            return False
        job.lease_until = _utcnow() + timedelta(seconds=lease_seconds)
        job.updated_at = _utcnow()
        return True

    def complete(self, job_id: UUID, owner: str) -> bool:
        job = self._jobs.get(job_id)
        if not job or job.lease_owner != owner:
            return False
        job.status = JobStatus.COMPLETED
        job.lease_owner = None
        job.lease_until = None
        job.updated_at = _utcnow()
        return True

    def fail(self, job_id: UUID, owner: str, error: str) -> bool:
        job = self._jobs.get(job_id)
        if not job or job.lease_owner != owner:
            return False
        job.last_error = error
        if job.attempt >= job.max_attempts:
            job.status = JobStatus.MANUAL_REVIEW
        else:
            job.status = JobStatus.PENDING
        job.lease_owner = None
        job.lease_until = None
        job.updated_at = _utcnow()
        return True

    def mark_manual_review(self, job_id: UUID, owner: str, reason: str) -> bool:
        job = self._jobs.get(job_id)
        if not job or job.lease_owner != owner:
            return False
        job.status = JobStatus.MANUAL_REVIEW
        job.last_error = reason
        job.lease_owner = None
        job.lease_until = None
        job.updated_at = _utcnow()
        return True

    def recover_expired(self) -> int:
        """Release expired leases back to PENDING. Returns count recovered."""
        now = _utcnow()
        n = 0
        for job in self._jobs.values():
            if (
                job.status == JobStatus.CLAIMED
                and job.lease_until is not None
                and job.lease_until < now
            ):
                job.status = JobStatus.PENDING
                job.lease_owner = None
                job.lease_until = None
                job.updated_at = now
                n += 1
        return n

    def get(self, job_id: UUID) -> OrderJob | None:
        return self._jobs.get(job_id)

    def list_by_status(self, status: JobStatus) -> list[OrderJob]:
        return [j for j in self._jobs.values() if j.status == status]

    def size(self) -> int:
        return len(self._jobs)
