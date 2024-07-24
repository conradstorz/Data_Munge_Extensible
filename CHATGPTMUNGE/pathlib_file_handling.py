"""These are the common functions for handling files in the manner I prefer."""

from loguru import logger
from pathlib import Path


@logger.catch()
def delete_file_and_verify(file_path):
    try:
        # Create a Path object
        file = Path(file_path)

        # Delete the file
        file.unlink()
        logger.info(f"Successfully deleted {file}")

        # Verify deletion
        if not file.exists():
            logger.info(f"Verification: {file} has been deleted.")
        else:
            logger.info(f"Verification failed: {file} still exists.")

    except FileNotFoundError:
        logger.info(f"Error: The file {file} does not exist.")
    except PermissionError:
        logger.info(f"Error: Permission denied. Unable to delete {file}.")
    except IsADirectoryError:
        logger.info(f"Error: {file} is a directory, not a file.")
    except OSError as e:
        logger.info(f"Error: An OS error occurred: {e}")
    except Exception as e:
        logger.info(f"An unexpected error occurred: {e}")


def move_file_with_check(source_path, destination_path, exist_ok=True):

    try:
        # Create Path objects
        source = Path(source_path)
        destination = Path(destination_path)

        logger.info(f'Moving {source.name} to {destination}')

        # Ensure the destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=exist_ok)

        # Move the file
        source.replace(destination)
        logger.info(f'Successfully moved {source} to {destination}')       

        # Verify the move
        if destination.exists() and not source.exists():
            logger.info(f"Move verified: {source} is now at {destination}")
        else:
            logger.info("Move verification failed.")

    except FileNotFoundError:
        logger.info(f"Error: The source file {source} does not exist.")
    except PermissionError:
        logger.info(f"Error: Permission denied. Unable to move {source} to {destination}.")
    except IsADirectoryError:
        logger.info(f"Error: {source} is a directory, not a file.")
    except OSError as e:
        logger.info(f"Error: An OS error occurred: {e}")
    except Exception as e:
        logger.info(f"An unexpected error occurred: {e}")
