import importlib
from pathlib import Path
from loguru import logger

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
        for script_file in self.scripts_directory.glob('*.py'):
            script_name = script_file.stem
            if 'handler' in script_name.lower():
                try:
                    module = importlib.import_module(f'{script_name}')
                    if hasattr(module, 'declaration') and hasattr(module, 'process'):
                        self.scripts[script_name] = {
                            'declaration': module.declaration,
                            'process': module.process
                        }
                        logger.info(f"Loaded script: {script_name}")
                    else:
                        logger.warning(f"Script {script_name} does not have required 'declaration' or 'process' attributes")
                except Exception as e:
                    logger.error(f"Failed to load script {script_name}: {e}")
        logger.info(f'{len(self.scripts)} data handling scripts loaded.')

    def get_script_for_file(self, filename):
        """
        Retrieves the processing function for a given filename based on script declarations.

        :param filename: Name of the file to match
        :type filename: str
        :return: Processing function if a matching script is found, None otherwise
        :rtype: function or None
        """
        logger.info(f"Getting script for file: {filename}")
        for script_name, script in self.scripts.items():
            if script['declaration'].matches(filename):
                logger.info(f"Match found: {script_name}")
                return script['process']
        logger.warning(f"No matching script found for file: {filename}")
        return None

# Example usage:
# scripts_manager = ScriptManager("/path/to/scripts")
# scripts_manager.load_scripts()