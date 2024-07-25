from pathlib import Path
from loguru import logger

class FileProcessor:
    """
    Processes files using the appropriate scripts managed by ScriptManager.

    :param script_manager: Instance of ScriptManager
    :type script_manager: ScriptManager
    """
    def __init__(self, script_manager):
        """
        Initializes the FileProcessor with the provided ScriptManager.

        :param script_manager: Instance of ScriptManager
        :type script_manager: ScriptManager
        """
        self.script_manager = script_manager

    def process(self, file_path):
        """
        Processes the specified file using the appropriate script.

        :param file_path: Path to the file to be processed
        :type file_path: str or Path
        """
        file_path = Path(file_path)
        if not Path(file_path).exists:
            logger.error(f"Function 'process' called with invalid file reference {file_path}.")
            return False
        
        logger.info(f"Processing file: {file_path}")
        process_func = self.script_manager.get_script_for_file(file_path.name)
        if not process_func:
            logger.warning(f"No matching script found for file: {file_path}")
            return False
        else:
            try:
                if process_func(file_path):
                    logger.info(f"Successfully processed file: {file_path}")
                else:
                    logger.error(f'Error processing {file_path}')
                    return False
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                return False
        return True
            

# Example usage:
# file_processor = FileProcessor(script_manager)
# file_processor.process("/path/to/file")