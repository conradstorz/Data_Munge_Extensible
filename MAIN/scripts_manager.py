import sys
import importlib
from pathlib import Path
from loguru import logger
import pprint


class ScriptManager:
    """
    Manages loading and retrieving scripts for processing files.

    :param scripts_directory: Directory containing the scripts
    :type scripts_directory: str or Path
    """

    def __init__(self, scripts_directory):
        """
        Initializes the ScriptManager with the specified directory.

        :param scripts_directory: Directory containing the scripts
        :type scripts_directory: str or Path
        """
        self.scripts_directory = Path(scripts_directory)
        self.scripts = {}
        self.load_scripts()

    def load_scripts(self):
        """
        Loads scripts from the specified directory. Scripts must have 'declaration' and 'process' attributes.
        """

        logger.info(f"Loading scripts from {self.scripts_directory}")

        for script_file in self.scripts_directory.glob("*.py"):
            script_name = script_file.stem
            if "handler" in script_name.lower():
                logger.info(f"Attempting to load handler {script_name}")
                try:
                    module = importlib.import_module(f"{script_name}")
                except Exception as e:
                    logger.error(f"Failed to import script {script_name}: {e}")
                else:  # no exception during import, continue
                    if hasattr(module, "declaration") and hasattr(
                        module, "handler_process"
                    ):
                        self.scripts[script_name] = {
                            "declaration": module.declaration,
                            "process": module.handler_process,
                        }
                        logger.info(f"Loaded script: {script_name}")
                    else:
                        logger.warning(
                            f"Script {script_name} does not have both required 'declaration' and 'handler_process' attributes, will not implement handler."
                        )

        logger.info(f"{len(self.scripts)} data handling scripts loaded.")
        if len(self.scripts) < 1:
            logger.error(f"No handlers loaded. Exiting")
            sys.exit(0)
        else:  # gather and log filename sub-strings that will be monitored
            filename_substrings = []
            for script_name, script in self.scripts.items():
                try:
                    filename_substrings.append(
                        f"{script_name}: {script['declaration'].get_filename_strings_to_match()}"
                    )
                except Exception as e:
                    logger.error(f"SCRIPT: {script_name}\n{e}")
            pretty_list_of_handlers = pprint.pformat(filename_substrings, width=160)
            logger.info(
                f"These are the templates and filename sub-strings being monitored during this run:\n{pretty_list_of_handlers}"
            )

    def get_script_for_file(self, filename):
        """
        Retrieves the processing function for a given filename based on script declarations.

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


# Example usage:
# scripts_manager = ScriptManager("/path/to/scripts")
# scripts_manager.load_scripts()
