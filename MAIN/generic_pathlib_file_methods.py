"""These are the common functions for handling files in the manner I prefer."""

from loguru import logger
from pathlib import Path
import re
import unicodedata

# List of valid extensions (expand as needed)
VALID_EXTENSIONS = {
    # Document formats
    '.txt', '.pdf', '.doc', '.docx', '.odt', '.rtf', '.tex', '.wpd',

    # Spreadsheet formats
    '.xls', '.xlsx', '.ods', '.csv',

    # Presentation formats
    '.ppt', '.pptx', '.odp',

    # Image formats
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',

    # Audio formats
    '.mp3', '.wav', '.aac', '.flac', '.ogg',

    # Video formats
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv',

    # Archive formats
    '.zip', '.tar', '.gz', '.rar', '.7z',

    # Code and markup formats
    '.html', '.css', '.js', '.py', '.java', '.c', '.cpp', '.xml', '.json', '.yml',

    # Other common formats
    '.iso', '.exe', '.dll'
}



def sanitize_filename(filename):
    """
    Sanitize a filename by removing or replacing invalid characters.
    This method normalizes the filename, removes any non-alphanumeric characters,
    and replaces spaces or hyphens with underscores. It also ensures that no
    periods are present in the filename unless it's part of a valid file extension.
    
    If no valid file extension is detected, the entire string is treated as the filename.
    
    :param filename: The original filename to sanitize.
    :type filename: str
    :return: The sanitized filename.
    :rtype: str
    """
    if not filename:
        logger.error("Filename is empty or None.")
        return None

    filepath = Path(filename)
    file_extension = filepath.suffix if filepath.suffix in VALID_EXTENSIONS else ''
    base_filename = filepath.stem if file_extension else filepath.name
    
    logger.debug(f"Sanitizing string: {base_filename}")
    
    # Normalize and sanitize the base filename
    base_filename = unicodedata.normalize('NFKD', base_filename).encode('ascii', 'ignore').decode('ascii')
    base_filename = re.sub(r'[^\w\s-]', '', base_filename).strip().lower()
    base_filename = re.sub(r'[-\s]+', '_', base_filename)
    
    # Remove any periods from the sanitized filename
    base_filename = base_filename.replace('.', '')
    
    logger.debug(f"Sanitized string: {base_filename}")
    
    # Return the sanitized filename with the valid file extension if one exists
    return f"{base_filename}{file_extension}"


@logger.catch()
def delete_file_and_verify(file_path):
    logger.debug(f'Attempting to delete file {file_path}')
    try:
        # Create a Path object
        file = Path(file_path)

        # Delete the file
        file.unlink()
        logger.debug(f"Successfully deleted {file}")

        # Verify deletion
        if not file.exists():
            logger.debug(f"Verification: {file} has been deleted.")
        else:
            logger.debug(f"Verification failed: {file} still exists.")

    except FileNotFoundError:
        logger.error(f"Error: The file {file} does not exist.")
    except PermissionError:
        logger.error(f"Error: Permission denied. Unable to delete {file}.")
    except IsADirectoryError:
        logger.error(f"Error: {file} is a directory, not a file.")
    except OSError as e:
        logger.error(f"Error: An OS error occurred: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


def move_file_with_check(source_path, destination_path, exist_ok=True):

    try:
        # Create Path objects
        source = Path(source_path)
        destination = Path(destination_path)

        logger.debug(f"Moving {source.name} to {destination}")

        # Ensure the destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=exist_ok)

        # Move the file
        source.replace(destination)
        logger.debug(f"Moved {source} to {destination}")

    # Verify the move
    if destination.exists() and not source.exists():
        logger.debug(f"Move verified: {source} was successfully moved to {destination}")
        return True
    else:
        if destination.exists() and source.exists():
            logger.debug(f"Move verification failed: {source} still exists at its original location, although {destination} was created.")
        elif not destination.exists() and source.exists():
            logger.debug(f"Move verification failed: {source} still exists at its original location, and {destination} was not created.")
        elif not destination.exists() and not source.exists():
            logger.debug(f"Move verification failed: Both {source} and {destination} do not exist.")
        return False


    except FileNotFoundError:
        logger.error(f"Error: The source file {source} does not exist.")
    except PermissionError:
        logger.error(f"Error: Permission denied. Unable to move {source} to {destination}.")
    except IsADirectoryError:
        logger.error(f"Error: {source} is a directory, not a file.")
    except OSError as e:
        logger.error(f"Error: An OS error occurred: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
