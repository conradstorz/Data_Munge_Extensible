"""These are the common functions for handling files in the manner I prefer."""

from loguru import logger
from pathlib import Path
import re
import unicodedata


def sanitize_filename(filename):
    """
    Sanitize a filename by removing or replacing invalid characters.

    This method normalizes the filename, removes any non-alphanumeric characters,
    and replaces spaces or hyphens with underscores.

    :param filename: The original filename to sanitize.
    :type filename: str
    :return: The sanitized filename.
    :rtype: str
    """
    filepath = Path(filename)
    filename = filepath.stem
    logger.debug(f"Sanitizing filename: {filename}")
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    filename = re.sub(r'[^\w\s-]', '', filename).strip().lower()
    filename = re.sub(r'[-\s]+', '_', filename)
    logger.debug(f"Sanitized filename: {filename}")
    return f"{filename}{filepath.suffix}"  # ensure that file extension doesn't get changed


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
        logger.debug(f"Successfully moved {source} to {destination}")

        # Verify the move
        if destination.exists() and not source.exists():
            logger.debug(f"Move verified: {source} is now at {destination}")
        else:
            logger.debug("Move verification failed.")

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
