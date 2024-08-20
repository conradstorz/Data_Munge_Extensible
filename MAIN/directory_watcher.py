import pickle
from pathlib import Path
from loguru import logger
import time

logger.catch()
def get_first_new_file(directory_to_watch, pickle_file):
    """
    Checks the download directory, removes missing filenames from pickle,
    and returns the first new filename it finds. Updates the pickle file.
        # NOTE: Edge Case: When my bank downloads data it uses the same name for all downloads on any given day and this stops the file from being processed.
        as such the workaround will be to manually rename the file when it arrives.

    :param directory_to_watch: Directory to monitor for new files
    :type directory_to_watch: str or Path
    :param pickle_file: Path to the pickle file for storing filenames
    :type pickle_file: str or Path
    :return: The first new filename found, or None if no new files
    :rtype: str or None
    """
    directory_to_watch = Path(directory_to_watch)
    pickle_file = Path(pickle_file)

    # Load existing filenames from pickle file
    if pickle_file.exists():
        with open(pickle_file, 'rb') as f:
            existing_files = set(pickle.load(f))
    else:
        existing_files = set()

    # Get current filenames in the directory
    current_files = {f.name for f in directory_to_watch.iterdir() if f.is_file()}

    # Find new files by comparing current files with existing files
    new_files = current_files - existing_files

    if new_files:
        # Pick the first new file
        new_file = new_files.pop()

        # Update pickle with the new file
        existing_files.add(new_file)
        with open(pickle_file, 'wb') as f:
            pickle.dump(existing_files, f)

        return Path(new_file)
    else:
        return None


@logger.catch()
def monitor_download_directory(directory_to_watch, file_processor, delay=1):

    logger.info(f"Starting directory watcher on {directory_to_watch}")

    try:
        while True:
            time.sleep(delay)
            logger.debug(f'Checking for new files in {directory_to_watch}')
            new_file = get_first_new_file(directory_to_watch, './download_history_file.pkl')
            logger.debug(f'found: {new_file}')
            if new_file:
                if Path(new_file).suffix not in ['.ini', '.tmp', '.png']:
                    file_processor.process(directory_to_watch / new_file)
                else:
                    logger.debug(f'Ignoring file found: {new_file}')

    except KeyboardInterrupt:
        logger.info(f'Keyboard interrupt detected.')
        logger.info("Directory watcher stopped")
    logger.info(f'All processes ended.')
    return True



# Example usage
new_file = get_first_new_file('./', './pickle_file.pkl')
if new_file:
    print(f"New file detected: {new_file}")
else:
    print("No new files detected.")

