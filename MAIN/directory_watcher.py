import pickle
from pathlib import Path
from loguru import logger
import time
import sys
from datetime import datetime

logger.catch()
def get_first_new_file(directory_to_watch, pickle_file):
    """
    Checks the download directory, renames new files by appending a timestamp,
    removes missing filenames from pickle, and returns the first new filename it finds. 
    Updates the pickle file.

    :param directory_to_watch: Directory to monitor for new files
    :type directory_to_watch: str or Path
    :param pickle_file: Path to the pickle file for storing filenames
    :type pickle_file: str or Path
    :return: The first new filename found, or None if no new files
    :rtype: str or None
    """
    directory_to_watch = Path(directory_to_watch)
    pickle_file = Path(pickle_file)

    # Load existing filenames from pickle
    if pickle_file.exists():
        with pickle_file.open('rb') as pf:
            existing_files = pickle.load(pf)
    else:
        existing_files = set()

    # Update the list of files in the directory
    current_files = set(directory_to_watch.iterdir())
    new_files = current_files - existing_files

    if not new_files:
        logger.info("No new files found.")
        return None

    # Process the first new file
    for new_file in new_files:
        if new_file.is_file():
            # Check for duplicate filenames and rename the file by appending a timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # If a file with the same name exists, append a timestamp to avoid conflicts
            new_filename = f"{new_file.stem}_{timestamp}{new_file.suffix}"
            new_file_path = directory_to_watch / new_filename
            
            # Loop to ensure no conflicts even after renaming
            while new_file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                new_filename = f"{new_file.stem}_{timestamp}{new_file.suffix}"
                new_file_path = directory_to_watch / new_filename
            
            new_file.rename(new_file_path)
            new_file = new_file_path
    
            new_filepath = new_file.with_name(new_filename)
            new_file.rename(new_filepath)
            logger.info(f"Renamed file: {new_file.name} -> {new_filename}")

            # Update the pickle file
            existing_files.add(new_filepath)
            with pickle_file.open('wb') as pf:
                pickle.dump(existing_files, pf)

            return str(new_filepath)

    return None

@logger.catch()
def monitor_download_directory(directory_to_watch, file_processor, delay=1):

    def indicate_progress(count):
        count =+ 1
        sys.stdout.write('.')
        sys.stdout.flush()    
        if count > 60:
            sys.stdout.write('\n')
            sys.stdout.flush()            
            count = 0              
        return count
    
    logger.info(f"Starting directory watcher on {directory_to_watch}")
    loops = 0
    try:
        while True:
            time.sleep(delay)  # Set the pace for how often to look for new files.
            loops = indicate_progress(loops)      
            new_file = get_first_new_file(
                directory_to_watch, "./download_history_file.pkl"
            )
            if new_file:
                if Path(new_file).suffix in [".ini", ".tmp", ".png"]:
                    logger.debug(f"Ignoring file found: {new_file}")
                else:                    
                    logger.info(f'File found to attempt processing {new_file}')
                    file_processor.process(directory_to_watch / new_file)

    except KeyboardInterrupt:
        logger.info(f"Keyboard interrupt detected.")
        logger.info("Directory watcher stopped")
    logger.info(f"All processes ended.")
    return True


# Example usage
new_file = get_first_new_file("./", "./pickle_file.pkl")
if new_file:
    print(f"New file detected: {new_file}")
else:
    print("No new files detected.")
