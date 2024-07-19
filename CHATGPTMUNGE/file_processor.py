import importlib

class FileProcessor:
    def __init__(self, script_manager):
        self.script_manager = script_manager

    def process(self, file_path):
        script_name = self.script_manager.get_script_for_file(file_path)
        if script_name:
            script_module = importlib.import_module(f'scripts.{script_name}')
            script_module.process(file_path)
        else:
            print(f"No matching script found for file: {file_path}")

# Example usage:
# file_processor = FileProcessor(script_manager)
# file_processor.process("/path/to/file")