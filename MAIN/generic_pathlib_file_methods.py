"""These are the common functions for handling files in the manner I prefer."""

from loguru import logger
from pathlib import Path
import re
import os
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

@logger.catch()
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

@logger.catch()
def move_file_with_check(source_path, destination_path, exist_ok=True):
    # move file to a new location
    logger.debug(f"Attempting to move {source_path} to {destination_path}")    
    # Create Path objects
    source = Path(source_path)
    destination = Path(destination_path)
    # check that paths are different
    if source == destination:
        logger.error(f"Error: Source {source} and destination {destination} are the same.")
        return False    
    try:
        # Ensure the destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=exist_ok)
        # Check if destination exists and handle based on exist_ok flag
        if destination.exists() and not exist_ok:
            logger.error(f"Error: Destination file {destination} already exists.")
            return False
        # Move the file
        source.replace(destination)
        logger.debug(f"Moved {source} to {destination}")
    except FileNotFoundError:
        logger.error(f"Error: The source file {source} does not exist.")
        return False
    except PermissionError:
        logger.error(f"Error: Permission denied. Unable to move {source} to {destination}.")
        return False
    except IsADirectoryError:
        logger.error(f"Error: {source} is a directory, not a file.")
        return False
    except OSError as e:
        logger.error(f"Error: An OS error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False
    # verify move took place and log any failures
    if destination.exists() and not source.exists():
        logger.debug(f"Move verified: {source} is now at {destination}")
        return True
    else:
        logger.debug("Move verification failed.")
        # Check if source file still exists
        if source.exists():
            logger.error(f"Verification failed: Source file {source} still exists, move did not occur.")
        # Check if destination file does not exist
        if not destination.exists():
            logger.error(f"Verification failed: Destination file {destination} does not exist.")
        # Check for partial move by comparing file sizes if source and destination both exist
        if source.exists() and destination.exists():
            source_size = os.path.getsize(source)
            destination_size = os.path.getsize(destination)
            if source_size != destination_size:
                logger.error(f"Verification failed: File sizes differ. Source: {source_size} bytes, Destination: {destination_size} bytes.")
            else:
                logger.error("Verification failed: Unknown issue, but sizes match. Further investigation needed.")
        # Additional check if destination exists but source does not (could indicate permission issues)
        if not source.exists() and not destination.exists():
            logger.error("Verification failed: Neither source nor destination exist. Possible permission or deletion issue.")
    return False
