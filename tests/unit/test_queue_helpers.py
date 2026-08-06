"""Pure helpers for queue lease timing."""
from datetime import datetime, timezone
from signal_bot.infrastructure.queue.jobs import lease_deadline

def test_lease_deadline_in_future():
    now = datetime.now(timezone.utc)
    deadline = lease_deadline(30)
    assert deadline > now
    assert 29 <= (deadline - now).total_seconds() <= 31
