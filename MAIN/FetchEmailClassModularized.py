"""A modularized class for monitoring email and saving JSON objects of email content."""

from imap_tools import MailBox, AND
import json
from pathlib import Path
from dotenv import dotenv_values
import time
from loguru import logger
from generic_pathlib_file_methods import sanitize_filename
import threading
from datetime import datetime


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
    :param ignore_file_types: A list of file SUFFIXs to ignore when downloading attachments.
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
        """
        try:
            with MailBox(self.imap_server).login(self.username, self.password, initial_folder="INBOX") as mailbox:
                for msg in mailbox.fetch(AND(seen=False) if not self.mark_as_seen else AND()):
                    self.process_email(msg)
                time.sleep(self.delay)
        except Exception as e:
            logger.error(f"Error fetching emails: {e}", exc_info=True)

    def process_email(self, msg):
        """
        Process an individual email.
        """
        # Process email details
        try:
            email_subject, email_sender, email_body = self.sanitize_email_details(msg)
        except Exception as e:
            logger.error(f"Error sanitizing email details for {msg.subject}: {e}", exc_info=True)
            return  # Stop processing if critical email details fail

        attachments = []

        # Construct email data
        try:
            email_data = self.construct_email_data(msg, email_subject, email_body, attachments)
        except Exception as e:
            logger.error(f"Error constructing email data for {email_subject}: {e}", exc_info=True)
            return  # Stop processing if email data can't be constructed

        # Save email content to JSON
        try:
            self.save_email_content(email_subject, email_data)
        except Exception as e:
            logger.error(f"Error saving email content for {email_subject}: {e}", exc_info=True)
            return  # Stop processing if saving email content fails

        # Process attachments
        try:
            self.process_attachments(msg.attachments, email_sender, attachments)
        except Exception as e:
            logger.error(f"Error processing attachments for {email_subject}: {e}", exc_info=True)

        logger.info(f"Processed and saved email: {email_subject}")


    def sanitize_email_details(self, msg):
        """
        Sanitize email details like subject and sender.
        """
        logger.info(f"Incoming eMail: '{msg.subject}' Sanitizing...")
        email_subject = sanitize_filename(msg.subject[:50])
        logger.debug(f'Sanitized eMail subject: "{email_subject}"')

        email_sender = sanitize_filename(msg.from_)
        logger.debug(f'Sanitized sender name: {email_sender}')

        email_body = msg.text or msg.html or "<No content>"
        return email_subject, email_sender, email_body

    def construct_email_data(self, msg, email_subject, email_body, attachments):
        """
        Construct the email data for saving as JSON.
        """
        return [{
            "subject": email_subject,
            "body": email_body,
            "from": msg.from_,
            "to": msg.to,
            "cc": msg.cc,
            "bcc": msg.bcc,
            "date": msg.date.isoformat(),
            "headers": dict(msg.headers),
            "attachments": attachments
        }]

    def save_email_content(self, email_subject, email_data):
        """
        Save the email content to a JSON file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(self.email_download_directory) / f"_CFSIV_email_{email_subject}_{timestamp}.json"

        logger.debug(f'Saving JSON file: {output_file}')
        with output_file.open('w') as f:
            json.dump(email_data, f, indent=4)

    def process_attachments(self, attachments_list, email_sender, attachments):
        """
        Process and save attachments from an email.
        """
        for att in attachments_list:
            logger.debug(f'Processing attachment: {att.filename=} size={att.size}')
            att_SUFFIX = att.filename.split(".")[-1].lower()

            if att_SUFFIX not in self.ignore_file_types:
                sanitized_filename = self.sanitize_attachment_filename(email_sender, att.filename)
                self.save_attachment(att, sanitized_filename)
                attachments.append({
                    "filename": sanitized_filename,
                    "content_type": att.content_type,
                    "size": att.size,
                    "saved_to": str(Path(self.email_download_directory) / sanitized_filename)
                })
            else:
                logger.debug(f"Ignored attachment with SUFFIX '{att_SUFFIX}': {att.filename}")

    def sanitize_attachment_filename(self, email_sender, filename):
        """
        Sanitize attachment filename for saving.
        """
        logger.debug(f'Sanitizing attachment filename: "{filename}"')
        return f"{email_sender}_{sanitize_filename(filename[:50])}"

    def save_attachment(self, att, sanitized_filename):
        """
        Save an individual attachment to disk.
        """
        attachment_destination = Path(self.email_download_directory) / sanitized_filename
        attachment_destination.parent.mkdir(parents=True, exist_ok=True)

        logger.debug(f'Saving attachment to: "{attachment_destination}"')
        with attachment_destination.open('wb') as f:
            f.write(att.payload)
        logger.debug(f"Processed and downloaded attachment: {attachment_destination}")

    def start(self):
        """
        Start the email fetching process in a separate thread.
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.fetch_emails)
            self.thread.start()
            logger.debug(f"Started email fetching for {self.username}")

    def stop(self):
        """
        Stop the email fetching process.
        """
        if self.running:
            self.running = False
            if self.thread is not None:
                self.thread.join()  # Wait for the thread to finish
            logger.debug(f"Stopped email fetching for {self.username}")

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
    