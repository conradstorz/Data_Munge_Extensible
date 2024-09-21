"""Classes to provide a method to store files
    with filenames of a maximum length 
    but with an original filename of a very long length 
    and then be able to locate those files again later.
"""
import re
import unicodedata
from datetime import datetime, timedelta
import json
from pathlib import Path
import shutil
import os
import fnmatch
import glob
from typing import List, Optional

class SlugGenerator:
    """
    Generates slugs for strings, applying cleaning, stop word removal, truncation, 
    and timestamping.

    :param max_length: Maximum length for the generated slug (default is 60).
    :type max_length: int
    :param stop_words: Optional set of stop words to remove from the slug.
    :type stop_words: set
    """
    def __init__(self, max_length=60, stop_words=None):
        self.max_length = max_length
        self.stop_words = stop_words or {"a", "an", "the", "is", "and", "or", "but", "on", "in", "with", "to", "of", "for", "at", "by"}

    def _normalize_string(self, input_string: str) -> str:
        """Normalize the string by converting to ASCII and removing accents."""
        normalized = unicodedata.normalize('NFKD', input_string)
        return normalized.encode('ascii', 'ignore').decode('ascii')

    def _clean_string(self, input_string: str) -> str:
        """Remove unwanted characters and replace spaces with underscores."""
        cleaned = re.sub(r'[^a-zA-Z0-9\s-]', '', input_string)
        cleaned = re.sub(r'[\s]+', '_', cleaned)  # Replace spaces with underscores
        return cleaned.strip('_')

    def _remove_stop_words(self, input_string: str) -> str:
        """Remove common short words from the string."""
        words = input_string.split('_')
        filtered_words = [word for word in words if word not in self.stop_words]
        return '_'.join(filtered_words)

    def _truncate_string(self, input_string: str) -> str:
        """Truncate the string to fit within the allowed length, accounting for a timestamp."""
        timestamp_length = len("_20240913_120000")  # Example format "_YYYYMMDD_HHMMSS"
        allowed_length = self.max_length - timestamp_length

        if len(input_string) > allowed_length:
            return input_string[:allowed_length].rsplit('_', 1)[0]  # Avoid cutting mid-word
        return input_string

    def generate(self, input_string: str) -> str:
        """
        Generate a slug from the input string by cleaning, removing stop words, truncating, 
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



class FileHandler:
    """
    Handles file operations such as copying files with slugified names and maintaining 
    a lookup table for original-to-slug mappings.

    :param slug_generator: An instance of SlugGenerator to create slugs.
    :type slug_generator: SlugGenerator
    :param lookup_filename: Name of the JSON file to store slug lookup mappings (default is 'slug_lookup.json').
    :type lookup_filename: str
    """
    def __init__(self, slug_generator: SlugGenerator, lookup_filename='slug_lookup.json'):
        self.slug_generator = slug_generator
        self.lookup_filename = lookup_filename

    def _load_lookup(self, directory: Path) -> dict:
        """Load the slug lookup table from the JSON file."""
        lookup_path = directory / self.lookup_filename
        if lookup_path.exists():
            with lookup_path.open('r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_lookup(self, directory: Path, lookup_table: dict) -> None:
        """Save the slug lookup table to the JSON file."""
        lookup_path = directory / self.lookup_filename
        with lookup_path.open('w', encoding='utf-8') as f:
            json.dump(lookup_table, f, indent=4, ensure_ascii=False)

    def copy_and_slug(self, file_path: Path, associated_string: str, destination_dir: Path) -> Path:
        """
        Copies a file to a destination directory using a slugified filename 
        and stores the mapping in a lookup table.

        :param file_path: Path to the original file.
        :type file_path: Path
        :param associated_string: String to be slugified for the filename.
        :type associated_string: str
        :param destination_dir: Destination directory where the file will be copied.
        :type destination_dir: Path
        :return: The path to the copied file with the slug filename.
        :rtype: Path
        """
        # Ensure destination directory exists
        destination_dir.mkdir(parents=True, exist_ok=True)

        # Generate slug filename
        slug_filename = self.slug_generator.generate(associated_string)
        new_file_path = destination_dir / (slug_filename + file_path.suffix)

        # Copy the file to the destination with the slugified name
        shutil.copy2(file_path, new_file_path)

        # Update lookup table
        lookup_table = self._load_lookup(destination_dir)
        lookup_table[slug_filename] = {
            "original_string": associated_string,
            "original_filename": file_path.name,
            "destination_filename": new_file_path.name
        }
        self._save_lookup(destination_dir, lookup_table)

        return new_file_path

    def decode_slug(self, slug_filename: str, destination_dir: Path) -> dict:
        """
        Retrieves the original filename and associated string from the lookup table 
        based on the slug filename.

        :param slug_filename: The slug filename to decode (without extension).
        :type slug_filename: str
        :param destination_dir: The directory where the lookup file is stored.
        :type destination_dir: Path
        :return: A dictionary containing the original filename and associated string.
        :rtype: dict
        """
        lookup_table = self._load_lookup(destination_dir)
        return lookup_table.get(slug_filename, {})


class FileLocator:
    """
    A class to locate files using various search methods.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize with an optional base directory.
        
        :param base_dir: The directory to search from. Defaults to the current working directory.
        :type base_dir: Path, optional
        """
        self.base_dir = base_dir or Path.cwd()

    def find_by_name(self, filename: str, search_in_subdirs: bool = False) -> List[Path]:
        """
        Locate a file by its name. Optionally search in subdirectories.
        
        :param filename: The name of the file to search for.
        :type filename: str
        :param search_in_subdirs: Whether to search in subdirectories (recursive search).
        :type search_in_subdirs: bool
        :return: List of matching file paths.
        :rtype: List[Path]
        """
        if search_in_subdirs:
            return list(self.base_dir.rglob(filename))
        return list(self.base_dir.glob(filename))

    def find_by_extension(self, extension: str, search_in_subdirs: bool = False) -> List[Path]:
        """
        Locate files by extension. Optionally search in subdirectories.
        
        :param extension: The file extension to search for (e.g., '.txt').
        :type extension: str
        :param search_in_subdirs: Whether to search in subdirectories (recursive search).
        :type search_in_subdirs: bool
        :return: List of matching file paths.
        :rtype: List[Path]
        """
        if not extension.startswith('.'):
            extension = f'.{extension}'
        pattern = f"*{extension}"
        
        if search_in_subdirs:
            return list(self.base_dir.rglob(pattern))
        return list(self.base_dir.glob(pattern))

    def find_by_wildcard(self, pattern: str, search_in_subdirs: bool = False) -> List[Path]:
        """
        Locate files using a wildcard pattern.
        
        :param pattern: The wildcard pattern to match (e.g., '*.txt', 'file*').
        :type pattern: str
        :param search_in_subdirs: Whether to search in subdirectories (recursive search).
        :type search_in_subdirs: bool
        :return: List of matching file paths.
        :rtype: List[Path]
        """
        if search_in_subdirs:
            return list(self.base_dir.rglob(pattern))
        return list(self.base_dir.glob(pattern))

    def find_by_fnmatch(self, pattern: str, search_in_subdirs: bool = False) -> List[Path]:
        """
        Locate files using Unix shell-style wildcards with fnmatch.
        
        :param pattern: The wildcard pattern to match (e.g., '*.txt', 'file*').
        :type pattern: str
        :param search_in_subdirs: Whether to search in subdirectories (recursive search).
        :type search_in_subdirs: bool
        :return: List of matching file paths.
        :rtype: List[Path]
        """
        matches = []
        if search_in_subdirs:
            for root, dirs, files in os.walk(self.base_dir):
                for filename in files:
                    if fnmatch.fnmatch(filename, pattern):
                        matches.append(Path(root) / filename)
        else:
            for file in self.base_dir.iterdir():
                if file.is_file() and fnmatch.fnmatch(file.name, pattern):
                    matches.append(file)
        return matches

    def find_using_glob(self, pattern: str) -> List[str]:
        """
        Locate files using the glob module (supports Unix-style patterns).
        
        :param pattern: The glob pattern to match.
        :type pattern: str
        :return: List of matching file paths.
        :rtype: List[str]
        """
        return glob.glob(str(self.base_dir / pattern))

    def find_in_env_path(self, filename: str) -> Optional[Path]:
        """
        Locate a file by searching through directories in the system's PATH environment variable.
        
        :param filename: The name of the file to search for in system PATH.
        :type filename: str
        :return: Path to the located file or None if not found.
        :rtype: Optional[Path]
        """
        for dir_path in os.getenv('PATH', '').split(os.pathsep):
            candidate = Path(dir_path) / filename
            if candidate.exists():
                return candidate
        return None

    def find_recent_files(self, days: int = 1, extension: Optional[str] = None) -> List[Path]:
        """
        Locate files that were modified within the last `n` days.
        
        :param days: The number of days to go back.
        :type days: int
        :param extension: Optional file extension to filter results (e.g., '.txt').
        :type extension: str, optional
        :return: List of matching file paths.
        :rtype: List[Path]
        """
        matches = []
        cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()

        for file in self.base_dir.rglob('*' if extension is None else f'*{extension}'):
            if file.is_file() and file.stat().st_mtime > cutoff_time:
                matches.append(file)
        return matches

    def find_largest_file(self) -> Optional[Path]:
        """
        Locate the largest file in the directory.

        :return: Path to the largest file or None if directory is empty.
        :rtype: Optional[Path]
        """
        files = [f for f in self.base_dir.rglob('*') if f.is_file()]
        if files:
            return max(files, key=lambda f: f.stat().st_size)
        return None


# Example of useage for the slugify and filehandler classes
if __name__ == "__main__":
    # Initialize a SlugGenerator instance
    slug_generator = SlugGenerator(max_length=60)

    # Initialize a FileHandler instance using the SlugGenerator
    file_handler = FileHandler(slug_generator=slug_generator)

    # Define the file to be slugified and copied
    # Use the current script's file (__file__) as the file to be slugified
    file_to_slug = Path(__file__)  # The file currently running this script
    associated_string = "Quarterly Financial Report for 2024"
    destination_directory = Path.cwd() / 'slugified_files'  # Destination directory

    # Use the FileHandler to copy the file with a slugified filename
    print(f"Original file path: {file_to_slug}")
    slugged_file_path = file_handler.copy_and_slug(file_to_slug, associated_string, destination_directory)
    print(f"Slugged file has been saved as: {slugged_file_path}")

    # Decode the slug to get the original filename and associated string
    slug_filename = slugged_file_path.stem  # Get the slug filename without extension
    decoded_info = file_handler.decode_slug(slug_filename, destination_directory)
    
    print(f"Decoded information for slug {slug_filename}:")
    print(f"Original Filename: {decoded_info.get('original_filename')}")
    print(f"Original String: {decoded_info.get('original_string')}")
    print(f"Destination Filename: {decoded_info.get('destination_filename')}")

    #################################

    # Example usage of file locator
    locator = FileLocator(base_dir=Path.cwd())

    # Find by filename
    print(locator.find_by_name('example.txt'))

    # Find by extension
    print(locator.find_by_extension('.txt', search_in_subdirs=True))

    # Find by wildcard pattern
    print(locator.find_by_wildcard('*.txt'))

    # Find using fnmatch pattern
    print(locator.find_by_fnmatch('example*'))

    # Find using glob
    print(locator.find_using_glob('*.py'))

    # Find in system PATH
    print(locator.find_in_env_path('python'))

    # Find recently modified files
    print(locator.find_recent_files(days=2, extension='.txt'))

    # Find largest file
    print(locator.find_largest_file())
