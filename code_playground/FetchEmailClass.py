"""A class for monitoring email and saving JSON objects of email content.
"""

from imap_tools import MailBox, AND
import json
import re
from pathlib import Path
from dotenv import dotenv_values
import unicodedata
import time


class EmailFetcher:
    def __init__(self, imap_server, username, password, mark_as_seen=False, delay=600):
        self.imap_server = imap_server
        self.username = username
        self.password = password
        self.mark_as_seen = mark_as_seen
        self.delay = delay

    def sanitize_filename(self, subject):
        """Sanitize the email subject to create a valid filename."""
        normalized_subject = unicodedata.normalize('NFKD', subject).encode('ascii', 'ignore').decode('ascii')
        invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
        safe_subject = re.sub(invalid_chars, '', normalized_subject)
        safe_subject = re.sub(r'\s+', '_', safe_subject)  # Replace spaces with underscores
        return safe_subject[:128]  # Limit filename length to avoid file system issues

    def get_email(self):
        """Fetches unseen emails from the inbox."""
        with MailBox(self.imap_server).login(self.username, self.password, 'INBOX') as mailbox:
            for msg in mailbox.fetch(AND(seen=False), mark_seen=self.mark_as_seen):
                email_parts = {
                    'subject': msg.subject,
                    'from': msg.from_,
                    'to': msg.to,
                    'date': msg.date_str,
                    'body': msg.text or msg.html,
                    'attachments': [att.filename for att in msg.attachments]
                }

                safe_subject = self.sanitize_filename(msg.subject)
                filename = f"email_{msg.uid}_{safe_subject}.json"

                json_output = json.dumps(email_parts, indent=4)

                # Save JSON to a file
                with open(filename, 'w') as json_file:
                    json_file.write(json_output)

    def run(self):
        """Continuously fetch emails as a long-running task."""
        try:
            while True:
                self.get_email()
                time.sleep(self.delay)
                # Add any other necessary delay or condition here
        except KeyboardInterrupt:
            print("EmailFetcher stopped.")



# example useage
if __name__ == "__main__":
    imap_server = "imap.gmail.com"
    # Email account credentials
    secrets_directory = Path(".env")
    secrets = dotenv_values(secrets_directory)

    username = secrets["EMAIL_USER"]
    password = secrets["EMAIL_PASSWORD"]

    # initiate class
    email_fetcher = EmailFetcher(imap_server, username, password)
    
    # start fetcher
    email_fetcher.run()

