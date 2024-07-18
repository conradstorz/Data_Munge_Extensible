import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

OBSERVED_TARGET = "D:/Users/Conrad/Downloads/"

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f'Event type: {event.event_type}  path : {event.src_path}')

if __name__ == "__main__":
    print('Starting')
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=Path(OBSERVED_TARGET), recursive=False)
    observer.start()
    print(f'Monitoring of: {OBSERVED_TARGET} begun')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Interrupt detected')
        observer.stop()
    observer.join()
    print('Ended nominally')
