"""A class for monitoring email and saving JSON objects of email content.
"""

"""A class for monitoring email and saving JSON objects of email content."""

from imap_tools import MailBox, AND
import json
import re
from pathlib import Path
from dotenv import dotenv_values
import unicodedata
import time
from loguru import logger


class EmailFetcher:
    def __init__(self, imap_server, username, password, mark_as_seen=False, delay=600):
        self.imap_server = imap_server
        self.username = username
        self.password = password
        self.mark_as_seen = mark_as_seen
        self.delay = delay

        logger.info("EmailFetcher initialized with server: {}, user: {}, mark_as_seen: {}, delay: {}",
                    imap_server, username, mark_as_seen, delay)

    def sanitize_filename(self, filename):
        """
        Sanitize the filename by removing or replacing invalid characters.
        """
        logger.debug("Sanitizing filename: {}", filename)
        filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
        filename = re.sub(r'[^\w\s-]', '', filename).strip().lower()
        filename = re.sub(r'[-\s]+', '_', filename)
        logger.debug("Sanitized filename: {}", filename)
        return filename

    def fetch_emails(self):
        try:
            with MailBox(self.imap_server).login(self.username, self.password) as mailbox:
                logger.info("Logged in to IMAP server: {}", self.imap_server)
                criteria = AND(seen=self.mark_as_seen)
                logger.debug("Fetching emails with criteria: {}", criteria)

                for msg in mailbox.fetch(criteria):
                    logger.info("Email fetched: Subject: {}, From: {}", msg.subject, msg.from_)
                    self.process_email(msg)
        except Exception as e:
            logger.error("An error occurred while fetching emails: {}", str(e))

    def process_email(self, msg):
        try:
            logger.debug("Processing email: {}", msg.subject)
            # Email processing logic here
            json_data = {
                'subject': msg.subject,
                'from': msg.from_,
                'date': msg.date.isoformat(),
                'text': msg.text,
                'html': msg.html,
                'attachments': [att.filename for att in msg.attachments]
            }
            filename = self.sanitize_filename(msg.subject) + '.json'
            self.save_json(json_data, filename)
            logger.info("Processed and saved email: {}", filename)
        except Exception as e:
            logger.error("An error occurred while processing email: {}", str(e))

    def save_json(self, data, filename):
        try:
            filepath = Path(filename)
            with filepath.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info("Saved JSON file: {}", filepath)
        except Exception as e:
            logger.error("An error occurred while saving JSON file: {}", str(e))

    def run(self):
        logger.info("Starting email fetcher")
        while True:
            self.fetch_emails()
            logger.info("Sleeping for {} seconds", self.delay)
            time.sleep(self.delay)



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

