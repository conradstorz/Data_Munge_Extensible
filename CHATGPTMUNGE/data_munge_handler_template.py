from loguru import logger
from pathlib import Path

# standardized declaration for CFSIV_Data_Munge_Extensible project
FILE_EXTENSION = ".qbo"
FILENAME_STRINGS_TO_MATCH = ["Export-", "dummy place holder for more matches in future"]


class Declaration:
    """
    Declaration for matching files to the script.

    :param filename: Name of the file to match
    :type filename: str
    :return: True if the script matches the file, False otherwise
    :rtype: bool
    """
    @logger.catch()
    def matches(self, filename: Path) -> bool:
        """Define how to match data files"""
        if any(s in filename for s in FILENAME_STRINGS_TO_MATCH) and filename.endswith(FILE_EXTENSION):
            # match found
            return True
        else:
            # no match
            return False

declaration = Declaration()


@logger.catch
def process(file_path: Path) -> bool:
    # This is the standardized function call for the Data_Handler_Template
    if not file_path.exists:
        logger.error(f'File to process does not exist.')
        return False
    else:
        # process file
        pass

    # all work complete
    return True
