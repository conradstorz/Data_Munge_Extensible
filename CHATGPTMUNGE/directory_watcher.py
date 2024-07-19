from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class DirectoryWatcher(FileSystemEventHandler):
    def __init__(self, directory_to_watch, file_processor):
        self.directory_to_watch = directory_to_watch
        self.file_processor = file_processor
        self.observer = Observer()

    def run(self):
        self.observer.schedule(self, self.directory_to_watch, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    def on_created(self, event):
        if not event.is_directory:
            self.file_processor.process(event.src_path)

# Example usage:
# file_processor = FileProcessor(script_manager)
# directory_watcher = DirectoryWatcher("/path/to/watch", file_processor)
# directory_watcher.run()