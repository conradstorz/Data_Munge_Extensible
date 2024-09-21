import re
import unicodedata
import json
from pathlib import Path
from datetime import datetime
import shutil

class Slugify:
    STOP_WORDS = {"a", "an", "the", "is", "and", "or", "but", "on", "in", "with", "to", "of", "for", "at", "by"}

    def __init__(self, max_length=60, lookup_filename='slug_lookup.json'):
        self.max_length = max_length
        self.lookup_filename = lookup_filename

    def _normalize_string(self, input_string: str) -> str:
        """Normalize the string, converting to ASCII and removing accents."""
        normalized = unicodedata.normalize('NFKD', input_string)
        return normalized.encode('ascii', 'ignore').decode('ascii')

    def _clean_string(self, input_string: str) -> str:
        """Clean the string, replacing unwanted characters with a hyphen."""
        cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', input_string)
        cleaned = re.sub(r'[\s]+', '_', cleaned)  # Replace spaces with underscores
        return cleaned.strip('_')

    def _remove_stop_words(self, input_string: str) -> str:
        """Remove common short words from the string (stop words)."""
        words = input_string.split('_')
        filtered_words = [word for word in words if word not in self.STOP_WORDS]
        return '_'.join(filtered_words)

    def _truncate_string(self, input_string: str) -> str:
        """Truncate the string to the specified max_length, accounting for timestamp."""
        timestamp_length = len("_20240913_120000")  # Example format "_YYYYMMDD_HHMMSS"
        allowed_length = self.max_length - timestamp_length

        if len(input_string) > allowed_length:
            return input_string[:allowed_length].rsplit('_', 1)[0]  # Avoid cutting mid-word
        return input_string

    def _generate_slug(self, input_string: str) -> str:
        """Generate the slug with timestamp."""
        normalized = self._normalize_string(input_string)
        cleaned = self._clean_string(normalized)
        cleaned_no_stop_words = self._remove_stop_words(cleaned.lower())
        truncated = self._truncate_string(cleaned_no_stop_words)

        timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
        return f"{truncated}{timestamp}"

    def encode(self, file_path: Path, associated_string: str, destination_dir: Path) -> Path:
        """
        Encodes the filename by generating a slug, copies the file to the destination
        with the new slug filename, and stores the mapping in the JSON lookup.
        """
        # Ensure destination directory exists
        destination_dir.mkdir(parents=True, exist_ok=True)

        # Generate slug filename
        slug_filename = self._generate_slug(associated_string)
        new_file_path = destination_dir / (slug_filename + file_path.suffix)

        # Copy the file to the new location with the slug filename
        shutil.copy2(file_path, new_file_path)

        # Update the lookup table with the new entry
        lookup_table = self._load_lookup(destination_dir)
        lookup_table[slug_filename] = {
            "original_string": associated_string,
            "original_filename": file_path.name,
            "destination_filename": new_file_path.name
        }
        self._save_lookup(destination_dir, lookup_table)

        return new_file_path

    def decode(self, slug_filename: str, destination_dir: Path) -> dict:
        """Returns the details associated with the slug filename from the lookup table."""
        lookup_table = self._load_lookup(destination_dir)
        return lookup_table.get(slug_filename, {})

    def _load_lookup(self, directory: Path) -> dict:
        """Load the lookup table from a JSON file."""
        lookup_path = directory / self.lookup_filename
        if lookup_path.exists():
            with lookup_path.open('r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_lookup(self, directory: Path, lookup_table: dict) -> None:
        """Save the lookup table to a JSON file."""
        lookup_path = directory / self.lookup_filename
        with lookup_path.open('w', encoding='utf-8') as f:
            json.dump(lookup_table, f, indent=4, ensure_ascii=False)


# Example usage
if __name__ == "__main__":
    slugger = Slugify(max_length=60)

    # Example of encoding a file
    file_to_slug = Path('rh_input.txt')
    destination_directory = Path.cwd() / Path('destination_folder')
    associated_string = "This is an example string for slugification"
    
    # Encode the file and generate the slugged filename
    slugged_file = slugger.encode(file_to_slug, associated_string, destination_directory)
    print(f"File has been slugged and saved as: {slugged_file}")

    # Example of decoding a slug filename
    slug_filename = slugged_file.stem  # Get slug without extension
    details = slugger.decode(slug_filename, destination_directory)
    print(f"Details for {slug_filename}: {details}")
