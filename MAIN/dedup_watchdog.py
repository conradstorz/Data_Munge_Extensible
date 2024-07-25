from time import perf_counter as pc
from typing import Any

import watchdog.events


class _DuplicateEventLimiter:
    """Duplicate event limiter.

    This class is responsible for limiting duplicated event detection. It works
    by comparing the timestamp of the previous event (if existent) to the
    current one, as well as the event itself. If the difference between the
    timestamps is less than a threshold and the events are the same, the event
    is considered a duplicate.
    """

    _DUPLICATE_THRESHOLD: float = 0.05

    def __init__(self) -> None:
        """Initialize a _DuplicateEventLimiter instance."""
        # Dummy event:
        self._last_event: dict[str, Any] = {
            "time": 0,
            "event": None
        }

    def _is_duplicate(self, event: watchdog.events.FileSystemEvent) -> bool:
        """Determine if an event is a duplicate.

        Args:
            event (watchdog.events.FileSystemEvent): event to check.

        Returns:
            bool: True if the event is a duplicate, False otherwise.
        """
        is_duplicate = (
            pc() - self._last_event["time"] < self._DUPLICATE_THRESHOLD
            and self._last_event["event"] == event
        )

        self._last_event = {
            "time": pc(),
            "event": event
        }

        return is_duplicate
    
class YourEventHandler(
        watchdog.events.RegexMatchingEventHandler,
        _DuplicateEventLimiter  ):
    # Inherit the class from the child.

    def __init__(self, ...):
        ...
        # Add _DuplicateEventLimiter init call on child init:
        _DuplicateEventLimiter.__init__(self)
        ...

    def on_modified(self, event):
        # Add this block at the top of the event handler method body:
        if self._is_duplicate(event):
            # Do whatever if event is duplicate.
            return  # Or just stop execution of the method.