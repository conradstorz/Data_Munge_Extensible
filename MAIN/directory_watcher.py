import pickle
from pathlib import Path
from loguru import logger
import time
import sys
from datetime import datetime
from generic_pathlib_file_methods import move_file_with_check
 
ARCHIVE_FOLDER = Path("D:/Users/Conrad/Downloads/Archive_misc/")  # for files that are ignored

logger.catch()
def get_first_new_file(directory_to_watch, pickle_file, ignore_SUFFIXs=None):
    """
    Checks the download directory, renames new files by appending a timestamp,
    removes missing filenames from pickle, and returns the first new filename it finds.
    Updates the pickle file.

    :param directory_to_watch: Directory to monitor for new files
    :type directory_to_watch: str or Path
    :param pickle_file: Path to the pickle file for storing filenames
    :type pickle_file: str or Path
    :param ignore_SUFFIXs: List of file SUFFIXs to ignore (e.g., ['.tmp', '.part'])
    :type ignore_SUFFIXs: list of str or None
    :return: The first new filename found, or None if no new files
    :rtype: str or None
    """
    def give_file_uniquie_name(filename, directry):
        # Loop to ensure no duplicate filename exists and rename the file by appending a timestamp to avoid conflicts
        new_file_path = filename.copy()
        while new_file_path.exists():  # TODO does this need to check for file/directory status?
            timestamp = datetime.now().strftime("%M%S")
            timestamp = f"({timestamp})"
            new_filename = f"{filename.stem}_{timestamp}{filename.suffix}"
            new_file_path = directry / new_filename

        return new_file_path


    directory_to_watch = Path(directory_to_watch)
    pickle_file = Path(pickle_file)
    ignore_SUFFIXs = ignore_SUFFIXs or []  # This is a good way to avoid the mutable variable problem
    #logger.debug(f'Checking watched directory {directory_to_watch} for new files while ignoring {ignore_SUFFIXs}')

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
        sys.exit(0)  # TODO re-raise error

    new_files = {f for f in current_files if f.name not in existing_files}

    if new_files == {}:
        logger.debug("No new files found.")
        # clean up any ignored files
        old_files = current_files - new_files
        for file in old_files:
            new_name = give_file_uniquie_name(file, directory_to_watch)
            file.rename(new_name)
            logger.debug(f"Renamed file: {file.name} -> {new_name}")
        return None

    # Process the first new file
    for new_file in new_files:
        logger.debug(f"New file found '{new_file.name}' in '{directory_to_watch.name}'")

        # Update the pickle file with the new filename
        existing_files.add(new_file)
        with pickle_file.open('wb') as pf:
            pickle.dump(existing_files, pf)

        if not (new_file.is_file() and new_file.suffix not in ignore_SUFFIXs):
            logger.debug('Ignoring.')
            continue

        new_file_path = give_file_uniquie_name(new_file, directory_to_watch)
        if new_file_path == new_file:
            return str(new_file_path)
        
        new_file.rename(new_file_path)
        logger.debug(f"Renamed file: {new_file.name} -> {new_file_path}")

        # Update the pickle file with the new filename
        existing_files.add(new_file_path)
        with pickle_file.open('wb') as pf:
            pickle.dump(existing_files, pf)

    return str(new_file_path)


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
            new_file = get_first_new_file(directory_to_watch, "./download_history_file.pkl", ignore_SUFFIXs=['.download', '.tmp', '.part', '.crdownload'])
            if new_file:
                time.sleep(1)  # allow the filesystem to settle before proceeding
                new_file = Path(new_file)
                if new_file.suffix in [".ini", ".png"]:
                    logger.debug(f"Ignoring file found: {new_file=}")
                    # Lets move this file to misc storage folder
                    new_file_path = Path(ARCHIVE_FOLDER) / new_file.stem
                    logger.debug(f"New destination: {new_file_path=}")
                    move_file_with_check(new_file, new_file_path)                    
                else:                    
                    logger.debug(f'File found to attempt processing {new_file}')
                    # Send this filename to be matched to a 'handler'
                    file_processor.process(directory_to_watch / new_file)
            loop = delay
            while loop > 0:  # Set the pace for how often to look for new files.
                time.sleep(0.1)  # Don't block processing of other code for more than 1 tenth of a second
                loop -= 0.1

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