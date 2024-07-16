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
    # Specify the directory you want to list
    specified_directory = Path("D:/Users/Conrad/Downloads")
    print(f"Specified directory: {specified_directory}")

    # List directories in the specified directory
    directories = list_directories(specified_directory)
    print("Directories in the specified directory:")
    for directory in directories:
        print(directory)

if __name__ == "__main__":
    main()