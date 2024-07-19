import importlib
from pathlib import Path

class ScriptManager:
    def __init__(self, scripts_directory):
        self.scripts_directory = Path(scripts_directory)
        self.scripts = {}
        self.load_scripts()

    def load_scripts(self):
        for script_file in self.scripts_directory.glob('*.py'):
            script_name = script_file.stem
            module = importlib.import_module(f'scripts.{script_name}')
            if hasattr(module, 'declaration') and hasattr(module, 'process'):
                self.scripts[script_name] = {
                    'declaration': module.declaration,
                    'process': module.process
                }

    def get_script_for_file(self, filename):
        for script_name, script in self.scripts.items():
            if script['declaration'].matches(filename):
                return script['process']
        return None

# Example usage:
# script_manager = ScriptManager("/path/to/scripts")
# script_manager.load_scripts()