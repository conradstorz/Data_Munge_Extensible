import os
import time
import csv
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyPDF2 import PdfFileReader

class Watcher:
    DIRECTORY_TO_WATCH = os.path('Downloads')
    # DIRECTORY_TO_WATCH = os.path.join(os.path.expanduser('~'), 'Downloads')
    print(f'Watching path: {DIRECTORY_TO_WATCH}')
    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=False)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

class Handler(FileSystemEventHandler):
    @staticmethod
    def on_created(event):
        if event.is_directory:
            return None
        elif event.src_path.endswith(".pdf"):
            print(f"New PDF file detected: {event.src_path}")
            extract_and_save_data(event.src_path)

def extract_and_save_data(pdf_path):
    try:
        with open(pdf_path, "rb") as file:
            reader = PdfFileReader(file)
            text = ""
            for page_num in range(reader.numPages):
                page = reader.getPage(page_num)
                text += page.extract_text()
        
        data = {"file_name": os.path.basename(pdf_path), "content": text}
        save_to_csv(data)
    except Exception as e:
        print(f"Failed to extract data from {pdf_path}: {e}")

def save_to_csv(data):
    csv_file = os.path.expanduser("~/Downloads/extracted_data.csv")
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["file_name", "content"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
    print(f"Data saved to {csv_file}")

if __name__ == "__main__":
    w = Watcher()
    try:
        w.run()
    except OSError as e:
        print(f"Error scheduling observer: {e}")
        # Handle the error or try an alternative method
