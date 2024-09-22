"""
This module contains common functions for handling files using the pathlib library.
"""

from loguru import logger
from pathlib import Path
import re
import os
import unicodedata

# List of valid extensions (expand as needed)
VALID_EXTENSIONS = {
    '.txt', '.pdf', '.doc', '.docx', '.odt', '.rtf', '.tex', '.wpd',
    '.xls', '.xlsx', '.ods', '.csv',
    '.ppt', '.pptx', '.odp',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
    '.mp3', '.wav', '.aac', '.flac', '.ogg',
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.html', '.css', '.js', '.py', '.java', '.c', '.cpp', '.xml', '.json', '.yml',
    '.iso', '.exe', '.dll'
}


@logger.catch()
def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.

    This method normalizes the filename, removes any non-alphanumeric characters,
    and replaces spaces or hyphens with underscores. It also ensures that no
    periods are present in the filename unless it's part of a valid file extension.

    :param filename: The original filename to sanitize.
    :type filename: str
    :return: The sanitized filename.
    :rtype: str
    :raises ValueError: If the filename is empty or None.
    """
    if not filename:
        logger.error("Filename is empty or None.")
        raise ValueError("Filename cannot be empty or None")

    filepath = Path(filename)
    file_extension = filepath.suffix if filepath.suffix in VALID_EXTENSIONS else ''
    base_filename = filepath.stem if file_extension else filepath.name

    logger.debug(f"Sanitizing string: {base_filename}")

    sanitized = unicodedata.normalize('NFKD', base_filename)
    sanitized = re.sub(r'[^\w\s-]', '', sanitized).strip().lower()
    sanitized = re.sub(r'[-\s]+', '_', sanitized)

    sanitized_filename = f"{sanitized}{file_extension}"

    logger.debug(f"Sanitized filename: {sanitized_filename}")
    return sanitized_filename


@logger.catch()
def is_valid_extension(file_extension: str) -> bool:
    """
    Validate whether the given file extension is in the predefined list of valid extensions.

    :param file_extension: The extension to validate.
    :type file_extension: str
    :return: True if the extension is valid, False otherwise.
    :rtype: bool
    """
    return file_extension in VALID_EXTENSIONS


@logger.catch()
def move_file(source: Path, destination: Path) -> bool:
    """
    Move a file from the source path to the destination path.

    If the destination directory does not exist, it will be created.
    The function also verifies that the move was successful by checking the existence
    of the source and destination files and comparing their sizes.

    :param source: The path to the source file.
    :type source: pathlib.Path
    :param destination: The path to the destination file.
    :type destination: pathlib.Path
    :return: True if the move is successful, False otherwise.
    :rtype: bool
    :raises FileNotFoundError: If the source file does not exist.
    :raises PermissionError: If permission is denied during the move.
    :raises IsADirectoryError: If the source is a directory, not a file.
    """
    if not source.exists():
        logger.error(f"Source file {source} does not exist.")
        raise FileNotFoundError(f"Source file {source} does not exist.")
    
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
        logger.debug(f"Moved {source} to {destination}")
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
    
    if destination.exists() and not source.exists():
        logger.debug(f"Move verified: {source} is now at {destination}")
        return True
    else:
        logger.debug("Move verification failed.")
        if source.exists():
            logger.error(f"Verification failed: Source file {source} still exists, move did not occur.")
        if not destination.exists():
            logger.error(f"Verification failed: Destination file {destination} does not exist.")
        if source.exists() and destination.exists():
            source_size = os.path.getsize(source)
            destination_size = os.path.getsize(destination)
            if source_size != destination_size:
                logger.error(f"File sizes differ. Source: {source_size} bytes, Destination: {destination_size} bytes.")
        return False


@logger.catch()
def delete_file_and_verify(file_path: Path) -> bool:
    """
    Delete the file at the given path and verify that the deletion was successful.

    :param file_path: The path to the file to delete.
    :type file_path: pathlib.Path
    :return: True if the file was successfully deleted, False otherwise.
    :rtype: bool
    :raises FileNotFoundError: If the file does not exist.
    :raises PermissionError: If permission is denied when trying to delete the file.
    """
    if not file_path.exists():
        logger.error(f"File {file_path} does not exist.")
        raise FileNotFoundError(f"File {file_path} does not exist.")
    
    try:
        file_path.unlink()
        logger.debug(f"Deleted file: {file_path}")
    except PermissionError:
        logger.error(f"Error: Permission denied. Unable to delete {file_path}.")
        return False
    except IsADirectoryError:
        logger.error(f"Error: {file_path} is a directory, not a file.")
        return False
    except OSError as e:
        logger.error(f"Error: An OS error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False

    if not file_path.exists():
        logger.debug(f"Deletion verified: {file_path} no longer exists.")
        return True
    else:
        logger.error(f"Verification failed: File {file_path} still exists after attempting deletion.")
        return False


@logger.catch()
def move_file_with_check(source: Path, destination: Path) -> bool:
    """
    Move a file from the source path to the destination path, with additional checks.

    This function performs the move and then validates that the move was successful
    by comparing file sizes or performing other checks.

    :param source: The path to the source file.
    :type source: pathlib.Path
    :param destination: The path to the destination file.
    :type destination: pathlib.Path
    :return: True if the move is successful, False otherwise.
    :rtype: bool
    :raises FileNotFoundError: If the source file does not exist.
    :raises PermissionError: If permission is denied during the move.
    :raises IsADirectoryError: If the source is a directory, not a file.
    """
    logger.debug(f"Attempting to move file from {source} to {destination}")

    if not move_file(source, destination):
        logger.error(f"Failed to move file from {source} to {destination}")
        return False

    # Verify the move
    if destination.exists() and not source.exists():
        logger.debug(f"Move successful and verified: {source} to {destination}")
        return True
    else:
        logger.error(f"Move verification failed for {source} to {destination}")
        return False
