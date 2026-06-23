from __future__ import annotations

import logging
import time
from typing import Callable, TypeVar


logger = logging.getLogger(__name__)

T = TypeVar("T")


def call_with_retry(
    func: Callable[[], T],
    *,
    max_retries: int,
    retry_delay: float,
    retry_name: str,
) -> T:
    delay = retry_delay
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= max_retries:
                raise
            logger.warning(
                "%s failed (%s). retrying in %.2fs (%d/%d)",
                retry_name,
                type(exc).__name__,
                delay,
                attempt + 1,
                max_retries,
            )
            time.sleep(delay)
            delay *= 2

    raise last_error  # pragma: no cover

