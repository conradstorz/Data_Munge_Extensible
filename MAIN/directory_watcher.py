from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import watchdog.events
from pathlib import Path
from loguru import logger
import time
from time import perf_counter as pc
from typing import Any

class _DuplicateEventLimiter:
    """Duplicate event limiter. (experimental)
    https://github.com/gorakhargosh/watchdog/issues/1003#issuecomment-1689069256
    This class is responsible for limiting duplicated event detection. It works
    by comparing the timestamp of the previous event (if existent) to the
    current one, as well as the event itself. If the difference between the
    timestamps is less than a threshold and the events are the same, the event
    is considered a duplicate.
    """

    _DUPLICATE_THRESHOLD: float = 0.09

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
        # log every event
        logger.debug(f'Checking duplicate status {event}')
        is_duplicate = (
            pc() - self._last_event["time"] < self._DUPLICATE_THRESHOLD
            and self._last_event["event"] == event
        )

        self._last_event = {
            "time": pc(),
            "event": event
        }

        return is_duplicate
    
class DirectoryWatcher(FileSystemEventHandler, _DuplicateEventLimiter):
    """
    Watches a directory for new files and processes them using FileProcessor.

    :param directory_to_watch: Directory to monitor for new files
    :type directory_to_watch: str or Path
    :param file_processor: Instance of FileProcessor
    :type file_processor: FileProcessor
    """
    def __init__(self, directory_to_watch, file_processor):
        """
        Initializes the DirectoryWatcher with the specified directory and FileProcessor.

        :param directory_to_watch: Directory to monitor for new files
        :type directory_to_watch: str or Path
        :param file_processor: Instance of FileProcessor
        :type file_processor: FileProcessor
        """
        _DuplicateEventLimiter.__init__(self) # Add _DuplicateEventLimiter init call on child init:
        self.directory_to_watch = Path(directory_to_watch)
        self.file_processor = file_processor
        self.observer = Observer()

    def run(self):
        """
        Starts the directory watcher.
        """
        logger.info(f"Starting directory watcher on {self.directory_to_watch}")
        self.observer.schedule(self, str(self.directory_to_watch), recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info(f'Keyboard interrupt detected.')
            self.observer.stop()
            logger.info("Directory watcher stopped")
        self.observer.join()
        logger.info(f'All processes ended.')

    def on_modified(self, event):
        """
        Event handler for newly created files.

        :param event: File system event
        :type event: watchdog.events.FileSystemEvent
        """
        # log every event
        logger.debug(f'Event: {event}')
        if self._is_duplicate(event):
            logger.debug(f'Watchdog found duplicate event. Ignoring.')
        else:
            if not event.is_directory:
                if Path(event.src_path).suffix not in ['.ini', '.tmp']:
                    logger.info(f"New file detected: {event.src_path}")
                    # give system time to settle file operations
                    if Path(event.src_path).exists:
                        logger.info(f'Sending file to be processed.')
                        self.file_processor.process(event.src_path)
                    else:
                        logger.error(f'File {event.src_path} does not exist.')
                        logger.error(f'Likely this is an echo event from the watchdog module and original file was already processed.')
                    logger.info(f'Returning to observation mode.')
                else:
                    logger.debug(f'Ignoring file {event.src_path}')

# Example usage:
# file_processor = FileProcessor(script_manager)
# directory_watcher = DirectoryWatcher("/path/to/watch", file_processor)
# directory_watcher.run()