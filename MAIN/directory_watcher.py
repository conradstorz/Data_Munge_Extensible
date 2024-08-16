import pickle
from pathlib import Path
def get_first_new_file(directory_to_watch, pickle_file):
    """
    Checks the download directory, removes missing filenames from pickle,
    and returns the first new filename it finds. Updates the pickle file.

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

        return new_file
    else:
        return None

# Example usage
new_file = get_first_new_file('./', './pickle_file.pkl')
if new_file:
    print(f"New file detected: {new_file}")
else:
    print("No new files detected.")