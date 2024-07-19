import importlib
import os

class ScriptManager:
    def __init__(self, scripts_directory):
        self.scripts_directory = scripts_directory
        self.scripts = {}
        self.load_scripts()

    def load_scripts(self):
        for filename in os.listdir(self.scripts_directory):
            if filename.endswith('.py'):
                script_name = filename[:-3]
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