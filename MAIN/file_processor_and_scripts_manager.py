
# Combined File: file_processor_and_scripts_manager.py

from pathlib import Path
from loguru import logger
import sys
import importlib
import pprint

class ScriptManager:
    """
    Manages loading and retrieving scripts for processing data.
    """

    def __init__(self, scripts_path):
        self.scripts_path = Path(scripts_path)
        self.scripts = {}

    def load_scripts(self):
        """
        Loads all the scripts from the specified directory.
        """
        logger.debug(f'Starting loading of scripts...')
        if not self.scripts_path.exists() or not self.scripts_path.is_dir():
            logger.error(f"Invalid scripts path: {self.scripts_path}")
            sys.exit(1)

        logger.info(f"Loading scripts from {self.scripts_path}")
        files = list(self.scripts_path.glob("*.py"))
        pretty_list_of_files = pprint.pformat(files, width=160)
        logger.debug(f'{pretty_list_of_files=}')
        
        for script_file in files:
            script_name = script_file.stem
            if "handler" in script_name.lower():
                logger.debug(f"Attempting to load handler {script_name}")
                try:
                    module = importlib.import_module(f"{script_name}")
                except Exception as e:
                    logger.error(f"Failed to import script {script_name}: {e}")
                else:  # no exception during import, continue
                    if hasattr(module, "declaration") and hasattr(
                        module, "data_handler_process"
                    ):
                        self.scripts[script_name] = {
                            "declaration": module.declaration,
                            "process": module.data_handler_process,
                        }
                        logger.info(f"Loaded script: {script_name}")
                    else:
                        logger.warning(f"Script {script_name} does not have both required 'declaration' and 'data_handler_process' attributes, will not implement handler.")

        logger.info(f"{len(self.scripts)} data handling scripts loaded.")
        if len(self.scripts) < 1:
            logger.error(f"No handlers loaded. Exiting")
            sys.exit(0)
        else:  # gather and log filename sub-strings that will be monitored
            filename_substrings = []
            for script_name, script in self.scripts.items():
                try:
                    filename_substrings.append(f"{script_name}: {script['declaration'].get_filename_strings_to_match()}")
                except Exception as e:
                    logger.error(f"SCRIPT: {script_name}\n{e}")
            pretty_list_of_handlers = pprint.pformat(filename_substrings, width=160)
            logger.debug(f"These are the templates and filename sub-strings being monitored during this run:\n{pretty_list_of_handlers}")


    def get_script_for_file(self, filename):
        """
        Retrieves the processing function for a given set of data based on 
            script declarations and filename pattern matching.

        :param filename: Name of the file to match
        :type filename: str
        :return: Processing function if a matching script is found, None otherwise
        :rtype: function or None
        """
        logger.info(f"Attempting to match script to file: {filename}")
        for script_name, script in self.scripts.items():
            if script["declaration"].matches(filename):
                logger.info(f"Script found: {script_name}")
                return script["process"]
        logger.warning(f"No matching script found for file: {filename}")
        return None


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
        if not file_path.exists():
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
                    logger.error(f"Error processing {file_path}")
                    return False
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                return False
        return True

# Example usage:
# scripts_manager = ScriptManager("/path/to/scripts")
# scripts_manager.load_scripts()
# file_processor = FileProcessor(scripts_manager)
# file_processor.process("/path/to/data/actual_file.data")

