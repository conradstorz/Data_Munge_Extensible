
import sys
import time
import importlib
from pathlib import Path
from loguru import logger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# This is our main loop class
class Watcher:
    DIRECTORY_TO_WATCH = Path("D:/Users/Conrad/Downloads/")

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = MyHandler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=False)
        self.observer.start()
        logger.info(f"Monitoring of: {self.DIRECTORY_TO_WATCH} begun")
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Interrupt detected")
            self.observer.stop()
        self.observer.join()


# This is how we recognize data when it arrives
class MyHandler(FileSystemEventHandler):
    @staticmethod
    def on_modified(event):
        if event.is_directory:
            return None
        else:
            # assume this is a file
            file = Path(event.src_path)
            if file.is_file():
                logger.info(f"New file detected: {file.name}")
                process_new_file(file, HANDLERS)
            else:
                logger.info(f"Unknown event detected {event}")
            return None


# Here we manipulate data when it arrives
@logger.catch()
def process_new_file(file_path, handlers):
    """This process will be called when the watcher has detected a file event.
    These events are very raw and can happen before the file is completely formed.
    This script will pause for five seconds to allow for the file to settle."""
    time.sleep(5)
    handler = None
    # Determine the file name and process using the appropriate handler
    filename = file_path.name
    names = handlers.keys()  # keys are the unique portion of the name of the data file
    for name in names:
        if name in filename:
            handler = handlers.get(name)
    if handler:
        handler.process(
            file_path
        )  # call the standardized function called 'process' to handle the file
    else:
        logger.info(f"No handler found for {file_path}")


@logger.catch()
def load_handlers():
    """Handler processes will define the unique substring within the filename that identifies them.
    Those strings are placed into a dictionary along with the module that processes that file.
    """
    # TODO find a way to allow some handlers to process ALL files regardless of filename
    #       like when a file extension is .qbo 
    HANDLERS = {}
    root = Path.cwd() / "MAIN"  # Gather python files in current working directory
    logger.info(f'Loading data handlers from: {root}')
    for file in root.glob("*.py"):
        name = str(file.stem)  # excludes the extension
        # look for files that self identify as 'Handlers'
        if "Handler" in name:
            # use the importlib package to capture this code
            module = importlib.import_module(name)
            # place the code into a dictionary
            HANDLERS[module.NAME_UNIQUE] = module
            if module.NAME_AKA:
                HANDLERS[module.NAME_AKA] = module
    logger.info(f"Load handlers function found {len(HANDLERS)} handlers.")
    if len(HANDLERS) < 1:
        logger.error(f'Insufficient handlers found to proceede. Exiting.')
        sys.exit(0)
    return HANDLERS


@logger.catch()
def main():
    logger.info("Starting watcher service")
    w = Watcher()  # initiate watcher
    try:
        w.run()  # run watcher
    except OSError as e:
        logger.info(f"Error scheduling observer: {e}")
    logger.info("Ended nominally")


if __name__ == "__main__":
    HANDLERS = load_handlers()
    main()
