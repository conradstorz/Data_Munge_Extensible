from loguru import logger

class Declaration:
    def matches(self, filename):
        return filename.endswith('.txt') or 'example' in filename

def process(file_path):
    logger.info(f"Processing {file_path} with example_script")
    print(f"Processing {file_path} with example_script")

declaration = Declaration()