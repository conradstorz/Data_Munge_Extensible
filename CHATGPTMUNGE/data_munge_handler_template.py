class Declaration:
    def matches(self, filename):
        return filename.endswith('.txt') or 'example' in filename

def process(file_path):
    print(f"Processing {file_path} with example_script")

declaration = Declaration()