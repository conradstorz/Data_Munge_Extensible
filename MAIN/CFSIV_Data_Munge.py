import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Watcher:
    DIRECTORY_TO_WATCH = os.path.expanduser("~/Downloads")

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

class Handler(FileSystemEventHandler):
    @staticmethod
    def on_created(event):
        if event.is_directory:
            return None
        else:
            print(f"New file detected: {event.src_path}")
            process_new_file(event.src_path)

def process_new_file(file_path):
    # Determine the file type and process using the appropriate handler
    file_extension = os.path.splitext(file_path)[1].lower()
    handler = HANDLERS.get(file_extension)
    if handler:
        handler.process(file_path)
    else:
        print(f"No handler found for {file_extension} files")

if __name__ == "__main__":
    w = Watcher()
    w.run()