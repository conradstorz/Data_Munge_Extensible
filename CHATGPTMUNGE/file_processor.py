from pathlib import Path
from loguru import logger

class FileProcessor:
    def __init__(self, script_manager):
        self.script_manager = script_manager

    def process(self, file_path):
        file_path = Path(file_path)
        logger.info(f"Processing file: {file_path}")
        process_func = self.script_manager.get_script_for_file(file_path.name)
        if process_func:
            try:
                process_func(file_path)
                logger.info(f"Successfully processed file: {file_path}")
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
        else:
            logger.warning(f"No matching script found for file: {file_path}")

# Example usage:
# file_processor = FileProcessor(script_manager)
# file_processor.process("/path/to/file")