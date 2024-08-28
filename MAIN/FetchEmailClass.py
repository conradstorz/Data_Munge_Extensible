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
    """
    A class to fetch emails from an IMAP server and save their content as JSON files.

    :param imap_server: The IMAP server address.
    :type imap_server: str
    :param username: The username to log in to the IMAP server.
    :type username: str
    :param password: The password to log in to the IMAP server.
    :type password: str
    :param mark_as_seen: Whether to mark emails as seen after fetching. Default is False.
    :type mark_as_seen: bool
    :param delay: The delay in seconds between each email fetching cycle. Default is 600 seconds.
    :type delay: int
    """

    def __init__(self, imap_server, username, password, mark_as_seen=False, delay=600):
        self.imap_server = imap_server
        self.username = username
        self.password = password
        self.mark_as_seen = mark_as_seen
        self.delay = delay

        logger.info(
            f"EmailFetcher initialized with server: {imap_server}, user: {username}, mark_as_seen: {mark_as_seen}, delay: {delay}"
        )

    def fetch_emails(self):
        """
        Fetch emails from the IMAP server based on the specified criteria.

        Emails are fetched based on whether they are marked as seen or not,
        depending on the `mark_as_seen` attribute. Each email is processed
        individually after being fetched.

        :raises Exception: If there is an error during the fetching process.
        """
        try:
            with MailBox(self.imap_server).login(self.username, self.password) as mailbox:
                logger.info(f"Logged in to IMAP server: {self.imap_server}")
                criteria = AND(seen=self.mark_as_seen)
                logger.debug(f"Fetching emails with criteria: {criteria}")

                for msg in mailbox.fetch(criteria):
                    logger.info(f"Email fetched: Subject: {msg.subject}, From: {msg.from_}")
                    self.process_email(msg)
        except Exception as e:
            logger.error(f"An error occurred while fetching emails: {str(e)}")

    def process_email(self, msg):
        """
        Process a single email message.

        This method extracts the subject, sender, date, text, HTML content, and
        attachments from the email. The email content is then saved as a JSON file
        using a sanitized version of the email's subject as the filename.

        :param msg: The email message to process.
        :type msg: imap_tools.message.Message
        :raises Exception: If there is an error during the processing of the email.
        """
        try:
            logger.debug(f"Processing email: {msg.subject}")
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
            logger.info(f"Processed and saved email: {filename}")
        except Exception as e:
            logger.error(f"An error occurred while processing email: {str(e)}")

    def save_json(self, data, filename):
        """
        Save the processed email data as a JSON file.

        The JSON file is saved with the specified filename in the current directory.

        :param data: The email data to save as JSON.
        :type data: dict
        :param filename: The filename to save the JSON data as.
        :type filename: str
        :raises Exception: If there is an error while saving the JSON file.
        """
        try:
            filepath = Path(filename)
            with filepath.open('w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved JSON file: {filepath}")
        except Exception as e:
            logger.error(f"An error occurred while saving JSON file: {str(e)}")

    def run(self):
        """
        Start the email fetching process.

        This method starts an infinite loop that repeatedly fetches emails
        at intervals specified by the `delay` attribute.

        :raises KeyboardInterrupt: If the process is interrupted manually.
        """
        logger.info("Starting email fetcher")
        while True:
            self.fetch_emails()
            logger.info(f"Sleeping for {self.delay} seconds")
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

