import os
from pathlib import Path

def list_directories(path):
    """
    List all directories in the given path.
    """
    try:
        # List all items in the given path
        items = os.listdir(path)
        directories = [item for item in items if os.path.isdir(os.path.join(path, item))]
        return directories
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return []

def main():
    # Get the current user's home directory
    home_directory = Path.home()
    print(f"Home directory: {home_directory}")

    # List directories in the home directory
    directories = list_directories(home_directory)
    print("Directories in the home directory:")
    for directory in directories:
        print(directory)

if __name__ == "__main__":
    main()