from loguru import logger

class Declaration:
    """
    Declaration for matching files to the script.

    :param filename: Name of the file to match
    :type filename: str
    :return: True if the script matches the file, False otherwise
    :rtype: bool
    """
    def matches(self, filename):
        return filename.endswith('.csv') or 'example' in filename

def process(file_path):
    """
    Processes the specified file.

    :param file_path: Path to the file to be processed
    :type file_path: Path
    """
    logger.info(f"Processing {file_path} with example_script")

declaration = Declaration()