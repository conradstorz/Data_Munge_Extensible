if __name__ == "__main__":
    from scripts_manager import ScriptManager
    from file_processor import FileProcessor
    from directory_watcher import DirectoryWatcher

    scripts_directory = "/path/to/scripts"
    directory_to_watch = "/path/to/watch"

    script_manager = ScriptManager(scripts_directory)
    file_processor = FileProcessor(script_manager)
    directory_watcher = DirectoryWatcher(directory_to_watch, file_processor)

    directory_watcher.run()