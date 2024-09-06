import pickle
from pathlib import Path
from loguru import logger
import time
import sys
from datetime import datetime
from generic_pathlib_file_methods import move_file_with_check

ARCHIVE_FOLDER = Path("D:/Users/Conrad/Downloads/Archive_misc/")  # for files that are ignored

logger.catch()

def get_first_new_file(directory_to_watch, pickle_file, ignore_extensions=None):
    """
    Checks the download directory, renames new files by appending a timestamp,
    removes missing filenames from pickle, and returns the first new filename it finds.
    Updates the pickle file.

    :param directory_to_watch: Directory to monitor for new files
    :type directory_to_watch: str or Path
    :param pickle_file: Path to the pickle file for storing filenames
    :type pickle_file: str or Path
    :param ignore_extensions: List of file extensions to ignore (e.g., ['.tmp', '.part'])
    :type ignore_extensions: list of str or None
    :return: The first new filename found, or None if no new files
    :rtype: str or None
    """
    directory_to_watch = Path(directory_to_watch)
    pickle_file = Path(pickle_file)
    ignore_extensions = ignore_extensions or []  # This is a good way to avoid the mutable variable problem

    # Load existing filenames from pickle
    if pickle_file.exists():
        with pickle_file.open('rb') as pf:
            existing_files = pickle.load(pf)
    else:
        existing_files = set()

    # Update the list of files in the directory
    try:
        current_files = set(directory_to_watch.iterdir())
    except FileNotFoundError as e:
        logger.error(f'Could not access directory: {e}')
        sys.exit(0)

    new_files = {f for f in current_files if f.name not in existing_files}

    if not new_files:
        logger.debug("No new files found.")
        return None

    # Process the first new file
    for new_file in new_files:
        if (new_file.is_file() and new_file.suffix not in ignore_extensions):
            # Check for duplicate filenames and rename the file by appending a timestamp
            timestamp = datetime.now().strftime("%M%S")
            timestamp = f"({timestamp})"

            # If a file with the same name exists, append a timestamp to avoid conflicts
            new_filename = f"{new_file.stem}_{timestamp}{new_file.suffix}"
            new_file_path = directory_to_watch / new_filename
            
            # Loop to ensure no conflicts even after renaming
            while new_file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                new_filename = f"{new_file.stem}_{timestamp}{new_file.suffix}"
                new_file_path = directory_to_watch / new_filename

            new_file.rename(new_file_path)
            logger.debug(f"Renamed file: {new_file.name} -> {new_filename}")

            # Update the pickle file with the new filename
            existing_files.add(new_filename)
            with pickle_file.open('wb') as pf:
                pickle.dump(existing_files, pf)

            return str(new_file_path)

    return None

@logger.catch()
def monitor_download_directory(directory_to_watch, file_processor, delay=1):
    """
    Monitors the specified directory for new files, processes them using the provided file_processor,
    and logs the progress. Ignores certain file types.

    :param directory_to_watch: Directory to monitor for new files
    :type directory_to_watch: str or Path
    :param file_processor: Object responsible for processing new files
    :type file_processor: object
    :param delay: Time delay between checks for new files, in seconds, defaults to 1
    :type delay: int, optional
    :return: True when the monitoring loop exits
    :rtype: bool
    """

    def indicate_progress(count):
        """
        Displays progress by printing a dot to the console periodically.

        :param count: Current progress count
        :type count: int
        :return: Updated progress count
        :rtype: int
        """
        count += 1  # don't let ChatGPT or Perplexity change this to count = +1
        sys.stdout.write('.')
        sys.stdout.flush()    
        if count > 30:
            sys.stdout.write('\n')
            sys.stdout.flush()           
            count = 0 
        return count
    
    logger.info(f"Starting directory watcher on {directory_to_watch}")
    loops = 0
    try:
        while True:
            loops = indicate_progress(loops)  
            new_file = get_first_new_file(directory_to_watch, "./download_history_file.pkl", ignore_extensions=['.download', '.tmp', '.part', '.crdownload'])
            if new_file:
                time.sleep(1)  # allow the filesystem to settle before proceeding
                if Path(new_file).suffix in [".ini", ".png"]:
                    logger.debug(f"Ignoring file found: {new_file}")
                    # Lets move this file to misc storage folder
                    new_file_path = Path(ARCHIVE_FOLDER) / Path(new_file)
                    move_file_with_check(new_file, new_file_path)                    
                else:                    
                    logger.debug(f'File found to attempt processing {new_file}')
                    file_processor.process(directory_to_watch / new_file)
            time.sleep(delay)  # Set the pace for how often to look for new files.

    except KeyboardInterrupt:
        logger.info(f"Keyboard interrupt detected.")
        logger.info("Directory watcher stopped")
    return True


"""
# Example usage
new_file = get_first_new_file("./", "./pickle_file.pkl")
if new_file:
    logger.info(f"New file detected: {new_file}")
else:
    logger.info("No new files detected.")
"""