from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    max_retries: int = 1

    def should_retry_json_repair(self, attempt: int) -> bool:
        return attempt < self.max_retries
