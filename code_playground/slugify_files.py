import re
import unicodedata
import json
from pathlib import Path
from datetime import datetime
import shutil

class Slugify:
    """
    A class to generate slug filenames, store lookup tables for slug-to-original mappings, 
    and handle file copying with new slug filenames.

    :param max_length: Maximum length for the generated slug, default is 60 characters.
    :type max_length: int
    :param lookup_filename: Filename of the JSON file to store slug lookup mappings, default is 'slug_lookup.json'.
    :type lookup_filename: str
    """
    STOP_WORDS = {"a", "an", "the", "is", "and", "or", "but", "on", "in", "with", "to", "of", "for", "at", "by"}

    def __init__(self, max_length=60, lookup_filename='slug_lookup.json'):
        """
        Initialize the Slugify instance with a maximum slug length and lookup file.
        
        :param max_length: Maximum length of the slug including timestamp (default is 60).
        :param lookup_filename: Name of the file storing the lookup table for slug mappings.
        """
        self.max_length = max_length
        self.lookup_filename = lookup_filename

    def _normalize_string(self, input_string: str) -> str:
        """
        Normalize the input string by converting it to ASCII and removing accents.

        :param input_string: The string to be normalized.
        :type input_string: str
        :return: Normalized ASCII string.
        :rtype: str
        """
        normalized = unicodedata.normalize('NFKD', input_string)
        return normalized.encode('ascii', 'ignore').decode('ascii')

    def _clean_string(self, input_string: str) -> str:
        """
        Clean the input string by removing unwanted characters and replacing spaces with underscores.

        :param input_string: The string to be cleaned.
        :type input_string: str
        :return: Cleaned string with non-alphanumeric characters removed.
        :rtype: str
        """
        cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', input_string)
        cleaned = re.sub(r'[\s]+', '_', cleaned)  # Replace spaces with underscores
        return cleaned.strip('_')

    def _remove_stop_words(self, input_string: str) -> str:
        """
        Remove common stop words from the input string.

        :param input_string: The string from which to remove stop words.
        :type input_string: str
        :return: String with stop words removed.
        :rtype: str
        """
        words = input_string.split('_')
        filtered_words = [word for word in words if word not in self.STOP_WORDS]
        return '_'.join(filtered_words)

    def _truncate_string(self, input_string: str) -> str:
        """
        Truncate the string to ensure it fits within the specified max length.
        Accounts for a timestamp in the format '_YYYYMMDD_HHMMSS'.

        :param input_string: The string to be truncated.
        :type input_string: str
        :return: Truncated string that fits within the allowed length.
        :rtype: str
        """
        timestamp_length = len("_20240913_120000")  # Example format "_YYYYMMDD_HHMMSS"
        allowed_length = self.max_length - timestamp_length

        if len(input_string) > allowed_length:
            return input_string[:allowed_length].rsplit('_', 1)[0]  # Avoid cutting mid-word
        return input_string

    def _generate_slug(self, input_string: str) -> str:
        """
        Generate a slug from the input string, cleaning, removing stop words, truncating, 
        and appending a timestamp.

        :param input_string: The string to slugify.
        :type input_string: str
        :return: Generated slug with a timestamp.
        :rtype: str
        """
        normalized = self._normalize_string(input_string)
        cleaned = self._clean_string(normalized)
        cleaned_no_stop_words = self._remove_stop_words(cleaned.lower())
        truncated = self._truncate_string(cleaned_no_stop_words)

        timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
        return f"{truncated}{timestamp}"

    def encode(self, file_path: Path, associated_string: str, destination_dir: Path) -> Path:
        """
        Encode the filename by generating a slug, copying the file to the destination directory
        with the new slug filename, and storing the mapping in a JSON lookup file.

        :param file_path: Path to the original file to be slugged and copied.
        :type file_path: Path
        :param associated_string: A string associated with the file for slug generation.
        :type associated_string: str
        :param destination_dir: Directory where the file will be copied with the new slug name.
        :type destination_dir: Path
        :return: Path to the copied file with the slug filename.
        :rtype: Path
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
        """
        Decode the slug filename by retrieving the associated details (original string, 
        original filename, destination filename) from the lookup table.

        :param slug_filename: The slug filename (without extension) to decode.
        :type slug_filename: str
        :param destination_dir: Directory where the lookup table is stored.
        :type destination_dir: Path
        :return: A dictionary containing details about the original file and string.
        :rtype: dict
        """
        lookup_table = self._load_lookup(destination_dir)
        return lookup_table.get(slug_filename, {})

    def _load_lookup(self, directory: Path) -> dict:
        """
        Load the slug lookup table from the JSON file.

        :param directory: Directory where the lookup table JSON file is stored.
        :type directory: Path
        :return: A dictionary representing the lookup table.
        :rtype: dict
        """
        lookup_path = directory / self.lookup_filename
        if lookup_path.exists():
            with lookup_path.open('r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_lookup(self, directory: Path, lookup_table: dict) -> None:
        """
        Save the lookup table to the JSON file.

        :param directory: Directory where the lookup table JSON file is stored.
        :type directory: Path
        :param lookup_table: The lookup table to save.
        :type lookup_table: dict
        """
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
