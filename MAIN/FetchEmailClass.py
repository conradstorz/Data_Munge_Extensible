"""A class for monitoring email and saving JSON objects of email content."""

from imap_tools import MailBox, AND
import json
from pathlib import Path
from dotenv import dotenv_values
import time
from loguru import logger
from generic_pathlib_file_methods import sanitize_filename
import threading

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

    def __init__(self, imap_server, username, password, mark_as_seen=False, interval=600):
        self.imap_server = imap_server
        self.username = username
        self.password = password
        self.mark_as_seen = mark_as_seen
        self.delay = interval
        self.running = False
        self.thread = None

        logger.info(
            f"EmailFetcher initialized with server: {imap_server}, user: {username}, mark_as_seen: {mark_as_seen}, delay: {interval}"
        )

    def fetch_emails(self):
        """
        Fetch emails from the IMAP server based on the specified criteria.

        Emails are fetched based on whether they are marked as seen or not,
        depending on the `mark_as_seen` attribute. Each email is processed
        individually after being fetched.

        :raises Exception: If there is an error during the fetching process.
        """
        while self.running:
            try:
                with MailBox(self.imap_server).login(self.username, self.password) as mailbox:
                    logger.info(f"Logged in to IMAP server: {self.imap_server}")
                    criteria = AND(seen=self.mark_as_seen)
                    logger.debug(f"Fetching emails with criteria: {criteria}")
                    for msg in mailbox.fetch(criteria):
                        self.process_email(msg)
                logger.info(f"Sleeping for {self.delay} seconds before the next fetch cycle.")
                time.sleep(self.delay)
            except Exception as e:
                logger.error(f"Error fetching emails: {str(e)}")

    def process_email(self, msg):
        """
        Process each email fetched from the server.

        The email content is sanitized and saved as a JSON file.

        :param msg: The email message object.
        :type msg: imap_tools.message.Message
        """
        # Example processing code - this should be replaced with actual processing logic
        email_subject = sanitize_filename(msg.subject)
        email_body = msg.text or msg.html

        # Example: Save the email content as a JSON file
        email_data = {
            "subject": email_subject,
            "body": email_body,
            "from": msg.from_,
            "date": msg.date.isoformat(),
        }
        output_file = Path(f"emails/{email_subject}.json")
        with open(output_file, 'w') as f:
            json.dump(email_data, f, indent=4)

        logger.info(f"Processed and saved email: {email_subject}")

    def start(self):
        """Start the email fetching process in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.fetch_emails)
            self.thread.start()
            logger.info(f"Started email fetching for {self.username}")

    def stop(self):
        """Stop the email fetching process."""
        if self.running:
            self.running = False
            if self.thread is not None:
                self.thread.join()  # Wait for the thread to finish
            logger.info(f"Stopped email fetching for {self.username}")


# Example usage (this part can be outside of the class in your script)
if __name__ == "__main__":
    email_fetcher = EmailFetcher("imap.server.com", "your_email@example.com", "password", mark_as_seen=False, interval=600)
    email_fetcher.start()

    # Do other processing here

    # To stop the email fetching process:
    email_fetcher.stop()
