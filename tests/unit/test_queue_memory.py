"""Unit tests for InMemoryJobQueue (Phase 4) – claim/lease/heartbeat/recovery/idempotency."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from signal_bot.domain.enums import JobStatus
from signal_bot.infrastructure.queue import InMemoryJobQueue


@pytest.fixture
def q() -> InMemoryJobQueue:
    return InMemoryJobQueue()


def test_enqueue_and_size(q):
    tid = uuid4()
    job = q.enqueue(trade_id=tid, job_type="entry", client_order_id="cid-1")
    assert job.status == JobStatus.PENDING
    assert q.size() == 1
    assert job.client_order_id == "cid-1"


def test_idempotent_client_order_id(q):
    tid = uuid4()
    j1 = q.enqueue(trade_id=tid, job_type="entry", client_order_id="same-cid")
    j2 = q.enqueue(trade_id=tid, job_type="entry", client_order_id="same-cid")
    assert j1.job_id == j2.job_id
    assert q.size() == 1


def test_claim_and_heartbeat(q):
    tid = uuid4()
    q.enqueue(trade_id=tid, job_type="entry")
    claimed = q.claim("worker-1", lease_seconds=30)
    assert claimed is not None
    assert claimed.status == JobStatus.CLAIMED
    assert claimed.lease_owner == "worker-1"
    assert claimed.attempt == 1
    assert claimed.lease_until is not None
    ok = q.heartbeat(claimed.job_id, "worker-1", lease_seconds=60)
    assert ok is True
    # wrong owner
    assert q.heartbeat(claimed.job_id, "other", lease_seconds=10) is False


def test_complete(q):
    tid = uuid4()
    q.enqueue(trade_id=tid, job_type="entry")
    claimed = q.claim("w1")
    assert claimed is not None
    assert q.complete(claimed.job_id, "w1") is True
    job = q.get(claimed.job_id)
    assert job is not None
    assert job.status == JobStatus.COMPLETED
    assert job.lease_owner is None


def test_fail_retries_then_manual_review(q):
    tid = uuid4()
    q.enqueue(trade_id=tid, job_type="entry", max_attempts=2)
    # attempt 1
    c1 = q.claim("w1")
    assert c1 is not None
    assert q.fail(c1.job_id, "w1", "timeout") is True
    j = q.get(c1.job_id)
    assert j is not None
    assert j.status == JobStatus.PENDING
    # attempt 2
    c2 = q.claim("w1")
    assert c2 is not None
    assert q.fail(c2.job_id, "w1", "again") is True
    j = q.get(c2.job_id)
    assert j is not None
    assert j.status == JobStatus.MANUAL_REVIEW


def test_recover_expired(q):
    tid = uuid4()
    q.enqueue(trade_id=tid, job_type="entry")
    claimed = q.claim("w1", lease_seconds=1)
    assert claimed is not None
    # force expiry
    claimed.lease_until = datetime.now(timezone.utc) - timedelta(seconds=5)
    n = q.recover_expired()
    assert n == 1
    j = q.get(claimed.job_id)
    assert j is not None
    assert j.status == JobStatus.PENDING
    assert j.lease_owner is None


def test_claim_none_when_empty(q):
    assert q.claim("w1") is None


def test_list_by_status(q):
    tid = uuid4()
    q.enqueue(trade_id=tid, job_type="a")
    q.enqueue(trade_id=tid, job_type="b")
    pending = q.list_by_status(JobStatus.PENDING)
    assert len(pending) == 2
