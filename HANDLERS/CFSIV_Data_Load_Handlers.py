import importlib
import os

HANDLERS = {}

def load_handlers():
    handlers_dir = os.path.join(os.path.dirname(__file__), 'handlers')
    for filename in os.listdir(handlers_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            module = importlib.import_module(f'handlers.{module_name}')
            HANDLERS[module.FILE_EXTENSION] = module

load_handlers()