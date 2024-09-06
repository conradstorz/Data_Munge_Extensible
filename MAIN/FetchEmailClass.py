"""A class for monitoring email and saving JSON objects of email content."""

from imap_tools import MailBox, AND
import json
from pathlib import Path
from dotenv import dotenv_values
import time
from loguru import logger
from generic_pathlib_file_methods import sanitize_filename
import threading
import sys

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
    :param ignore_file_types: A list of file extensions to ignore when downloading attachments.
    :type ignore_file_types: list
    """

    def __init__(self, imap_server, username, password, mark_as_seen=False, interval=600, ignore_file_types=None, dld=""):
        if ignore_file_types is None:
            ignore_file_types = ["gif"]
        
        self.imap_server = imap_server
        self.username = username
        self.password = password
        self.mark_as_seen = mark_as_seen
        self.delay = interval
        self.email_download_directory = dld
        self.ignore_file_types = [ext.lower() for ext in ignore_file_types]
        self.running = False
        self.thread = None

        logger.debug(
            f"EmailFetcher initialized with server: {imap_server}, user: {username}, mark_as_seen: {mark_as_seen}, delay: {interval}, ignore_file_types: {self.ignore_file_types}"
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
            while self.running:
                with MailBox(self.imap_server).login(self.username, self.password) as mailbox:
                    sys.stdout.write('\n')  # Start a newline on the console (to ensure next output is at the first character position)
                    logger.info("Checking eMail")
                    criteria = AND(seen=self.mark_as_seen)
                    logger.debug(f"Fetching emails with criteria: {criteria}")
                    for msg in mailbox.fetch(criteria):
                        self.process_email(msg)
                    logger.debug('IMAP connection closed.')
                # Instead of sleeping for the full delay, sleep in short intervals to avoid blocking behaviour
                sleep_interval = 1  # seconds
                elapsed_time = 0

                while elapsed_time < self.delay:
                    if not self.running:
                        break
                    time.sleep(sleep_interval)
                    elapsed_time += sleep_interval
                logger.debug(f"Completed eMail rest period {elapsed_time} seconds in {sleep_interval} second increments.")
                
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")


    def process_email(self, msg):
        """
        Process each email fetched from the server.

        The email content is sanitized and saved as a JSON file. Attachments are downloaded
        if they do not match the ignore file types list.

        :param msg: The email message object.
        :type msg: imap_tools.message.Message
        """
        try:
            # gather email details and sanitize strings
            logger.info(f"Incoming eMail: '{msg.subject}' Sanitizing...")
            email_subject = sanitize_filename(msg.subject)
            logger.debug(f'Sanitized eMail subject: "{email_subject}"')
            email_sender = sanitize_filename(msg.from_)
            logger.debug(f'Sanitized sender name: {email_sender}')
            email_body = msg.text or msg.html
            attachments = []

            # Construct the email data
            email_data = [ {
                "subject": email_subject,
                "body": email_body,
                "from": msg.from_,
                "to": msg.to,
                "cc": msg.cc,
                "bcc": msg.bcc,
                "date": msg.date.isoformat(),
                "headers": dict(msg.headers),
                "attachments": attachments
            } ]

            # Save email content as JSON
            output_file = Path(self.email_download_directory) / Path(f"_CFSIV_email_{email_subject}.json")
            logger.debug(f'Saving JSON file: {output_file}')
            with output_file.open('w') as f:
                json.dump(email_data, f, indent=4)

            # Process and download attachments
            for att in msg.attachments:
                logger.debug(f'Processing attachment: {att.filename=}')
                att_extension = att.filename.split(".")[-1].lower()
                
                if att_extension not in self.ignore_file_types:
                    logger.debug(f'Sanitizing attachment filename: "{att.filename}"')
                    sanitized_filename = f"{email_sender}_{sanitize_filename(att.filename)}"
                    attachment_destination = Path(self.email_download_directory) / Path(sanitized_filename)
                    attachment_destination.parent.mkdir(parents=True, exist_ok=True)
                    
                    logger.debug(f'Saving attachment to: "{attachment_destination}"')
                    with attachment_destination.open('wb') as f:
                        f.write(att.payload)
                    
                    logger.debug(f"Processed and downloaded attachment: {attachment_destination}")
                    attachments.append({
                        "filename": sanitized_filename,
                        "content_type": att.content_type,
                        "size": att.size,
                        "saved_to": str(attachment_destination)
                    })
                else:
                    logger.debug(f"Ignored attachment with extension '{att_extension}': {att.filename}")

            
            logger.info(f"Processed and saved email: {email_subject}")

        except Exception as e:
            logger.error(f"Error processing email {msg.subject}: {e}")


    def start(self):
        """Start the email fetching process in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.fetch_emails)
            self.thread.start()
            logger.debug(f"Started email fetching for {self.username}")


    def stop(self):
        """Stop the email fetching process."""
        if self.running:
            self.running = False
            if self.thread is not None:
                self.thread.join()  # Wait for the thread to finish
            logger.debug(f"Stopped email fetching for {self.username}")


# Example usage (this part can be outside of the class in your script)
if __name__ == "__main__":
    email_fetcher = EmailFetcher(
        "imap.server.com", 
        "your_email@example.com", 
        "password", 
        mark_as_seen=False, 
        interval=600, 
        ignore_file_types=["gif", "bmp"]
    )
    email_fetcher.start()

    # Do other processing here

    # To stop the email fetching process:
    email_fetcher.stop()
