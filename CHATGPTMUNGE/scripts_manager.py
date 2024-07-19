import importlib
from pathlib import Path
from loguru import logger

class ScriptManager:
    def __init__(self, scripts_directory):
        self.scripts_directory = Path(scripts_directory)
        self.scripts = {}
        self.load_scripts()

    def load_scripts(self):
        logger.info(f"Loading scripts from {self.scripts_directory}")
        for script_file in self.scripts_directory.glob('*.py'):
            script_name = script_file.stem
            try:
                module = importlib.import_module(f'scripts.{script_name}')
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

    def get_script_for_file(self, filename):
        logger.info(f"Getting script for file: {filename}")
        for script_name, script in self.scripts.items():
            if script['declaration'].matches(filename):
                logger.info(f"Match found: {script_name}")
                return script['process']
        logger.warning(f"No matching script found for file: {filename}")
        return None

# Example usage:
# script_manager = ScriptManager("/path/to/scripts")
# script_manager.load_scripts()