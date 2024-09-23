import pytest
from datetime import datetime
from MAIN.slugify_file_manager import SlugGenerator, FileHandler  # Assuming this is the module name

@pytest.fixture
def slug_generator():
    return SlugGenerator(max_length=60)

@pytest.fixture
def file_handler(slug_generator):
    return FileHandler(slug_generator=slug_generator)

@pytest.fixture
def temp_file(tmp_path):
    # Create a temporary file for testing
    file = tmp_path / "testfile.txt"
    file.write_text("This is some test content.")
    return file

@pytest.fixture
def associated_string():
    return "Test document for slugging"

def test_slug_generator(slug_generator):
    input_string = "Sample input for generating a slug"
    slug = slug_generator.generate(input_string)

    assert isinstance(slug, str), "Slug should be a string"
    assert len(slug) <= 60, "Slug should not exceed max length"
    assert "_" in slug, "Slug should contain underscores"

    # Get current timestamp and check that the slug ends with it in "_YYYYMMDD_HHMMSS" format
    current_timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
    assert slug.endswith(current_timestamp), "Slug should have a timestamp in the format _YYYYMMDD_HHMMSS"

def test_file_handler_copy_and_slug(file_handler, temp_file, associated_string, tmp_path):
    destination_dir = tmp_path / "slugified_files"
    destination_dir.mkdir()

    # Perform the copy and slugging
    slugged_file_path = file_handler.copy_and_slug(temp_file, associated_string, destination_dir)

    assert slugged_file_path.exists(), "Slugged file should exist"
    assert slugged_file_path.suffix == ".txt", "Slugged file should keep the original file SUFFIX"
    assert len(slugged_file_path.stem) <= 60, "Slugged filename should not exceed max length"

def test_file_handler_decode_slug(file_handler, temp_file, associated_string, tmp_path):
    destination_dir = tmp_path / "slugified_files"
    destination_dir.mkdir()

    # Perform the copy and slugging
    slugged_file_path = file_handler.copy_and_slug(temp_file, associated_string, destination_dir)

    # Get the slug filename and decode it
    slug_filename = slugged_file_path.stem
    decoded_info = file_handler.decode_slug(slug_filename, destination_dir)

    assert decoded_info['original_filename'] == temp_file.name, "Original filename should match"
    assert decoded_info['original_string'] == associated_string, "Original string should match"
    assert decoded_info['destination_filename'] == slugged_file_path.name, "Destination filename should match slugged file"

