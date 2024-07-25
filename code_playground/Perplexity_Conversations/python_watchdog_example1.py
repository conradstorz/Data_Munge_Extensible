# This code generated with Perplexity and roughed out on 7/16/2024
""" Monitor a path for changes and provide hooks for optional processing.
The original purpose of this script is to monitor my downloads directory for files that require post-download processing. 
The first example of this is banking transactions from my bank. I need to swap memo and name fields while removing useless characters.
The second example is when I download data from my jukebox provider TouchTunes and I want to convert a PDF into a CSV file.
I'm attempting here to create a framework that I can expand easily when new use-cases arrise.
This code will find files that match a pattern and then launch a custom script that can munge the data as needed.
There will be a sub-directory of the working directory of this script that contains file handlers for each use case.
"""
import os
import sys
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# from watchdog.observers.polling import PollingObserver
# PollingObserver was not witnessing ALL events under windows running inside of VScode terminal
from loguru import logger

# constants
RUNTIME_NAME = Path(__file__)
CSV_EXT = [".csv"]
EXCEL_EXT = [".xls"]
DL_DRIVE = "D:"
DL_USER_BASE = "Users"
DL_USER = "Conrad"
DL_DIRECTORY = "Downloads"
DL_PATH = Path("D:/Users/Conrad/Downloads/")

# Configure Loguru logger
logger.remove()  # Remove default handler
logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")
logger.add("./LOGS/file_{time}.log", rotation="10 MB", retention="10 days", level="DEBUG")

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # Log any file system event
        logger.info(f"Event type: {event.event_type}  path: {event.src_path}")
        if event.is_directory:
            logger.debug("It's a directory event")
        else:
            logger.debug("It's a file event")
        try:
            pass # Here you can add your custom logic to handle different event types
        except Exception as e:
            logger.exception(f"Error handling event: {e}")

class WatchdogRunner:
    def __init__(self, path):
        self.path = path
        self.observer = None
        self.handler = MyHandler()
        self.stopped = False

    def start(self):
        logger.info(f"Starting to watch: {self.path}")
        self.setup_observer()

    def setup_observer(self):
        try:
            # Use PollingObserver for better cross-platform support
            self.observer = Observer()
            self.observer.schedule(self.handler, self.path, recursive=False)
            self.observer.start()
            logger.debug("Observer started")
        except Exception as e:
            logger.exception(f"Error setting up observer: {e}")
            self.stopped = True


    def stop(self):
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join()
                logger.debug("Observer stopped")
            except Exception as e:
                logger.exception(f"Error stopping observer: {e}")
        self.stopped = True

    def run(self):
        self.start()
        try:
            while not self.stopped:
                try:
                    # Check if the observer is still alive
                    if not self.observer.is_alive():
                        logger.warning("Observer not alive, restarting...")
                        self.stop()
                        self.setup_observer()
                    
                    # Check if the watched directory still exists
                    if not os.path.exists(self.path):
                        logger.warning(f"Watched path {self.path} does not exist. Waiting...")
                        time.sleep(10)  # Wait before checking again
                        continue

                    time.sleep(1)
                except Exception as e:
                    logger.exception(f"Error in main loop: {e}")
                    time.sleep(5)  # Wait before retrying
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Stopping...")
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
        finally:
            self.stop()

if __name__ == "__main__":
    # Get the directory to watch from command line arguments or use current directory
    try:
        watch_path = sys.argv[1] if len(sys.argv) > 1 else DL_PATH
        
        # Ensure the watch path exists
        if not os.path.exists(watch_path):
            logger.error(f"The specified path does not exist: {watch_path}")
            sys.exit(1)

        runner = WatchdogRunner(watch_path)
        runner.run()
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)