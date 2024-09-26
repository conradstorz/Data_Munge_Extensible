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
        self.delay = interval
        self.mark_as_seen = mark_as_seen
        self.email_download_directory = dld
        self.ignore_file_types = ignore_file_types if ignore_file_types else []
        self.thread = None
        self.stop_thread = threading.Event()

        logger.debug(
            f"EmailFetcher initialized with server: {imap_server}, user: {username}, mark_as_seen: {mark_as_seen}, delay: {interval}, ignore_file_types: {self.ignore_file_types}"
        )

    def fetch_emails(self):
        """Fetch emails in a loop, logging errors, and handling thread safety."""
        try:
            while not self.stop_thread.is_set():
                with MailBox(self.imap_server).login(self.username, self.password) as mailbox:
                    criteria = AND(seen=self.mark_as_seen)
                    logger.debug(f"Fetching emails with criteria: {criteria}")
                    for msg in mailbox.fetch(criteria):    
                        self.process_email(msg)
                        # Check again if stop_thread is set frequently
                        if self.stop_thread.is_set():
                            break                                 
                    logger.debug('IMAP connection closed.')

                loop = self.delay
                while loop > 0:
                    loop -= 1
                    # Check again if stop_thread is set frequently
                    if self.stop_thread.is_set():
                        break                        
                    time.sleep(1)

        except Exception as e:
            logger.exception(f"An error occurred during email fetching: {e}")
        finally:
            logger.info("Email fetching thread has exited.")


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
        # Ensure the directory exists before saving the file
        attachment_destination = Path(self.email_download_directory) / sanitized_filename
        try:
            logger.debug(f'Creating directory if it does not exist: "{attachment_destination.parent}"')
            attachment_destination.parent.mkdir(parents=True, exist_ok=True)

            logger.debug(f'Saving attachment to: "{attachment_destination}"')
            with attachment_destination.open('wb') as f:
                f.write(att.payload)
            logger.debug(f"Processed and downloaded attachment: {attachment_destination}")
        
        except Exception as e:
            logger.error(f"Failed to save attachment {sanitized_filename} at {attachment_destination}: {e}", exc_info=True)
            raise


    def start_fetching(self):
        """Start the email fetching process in a separate thread."""
        if self.thread is None or not self.thread.is_alive():
            logger.info("Starting email fetching thread.")
            self.thread = threading.Thread(target=self.fetch_emails)
            self.thread.start()

            # Start the monitoring in a separate thread
            logger.debug(f"Starting the fetching monitor in its own thread.")
            self.monitoring_thread = threading.Thread(target=self.monitor_thread)
            self.monitoring_thread.start()
        else:
            logger.warning("Email fetching thread is already running.")

    def monitor_thread(self):
        """Monitor the thread and restart if it stalls."""
        while not self.stop_thread.is_set():  # Respect the stop signal
            time.sleep(1)  # Check thread status every 60 seconds
            if not self.thread.is_alive():
                logger.error("Thread has stalled, attempting to restart.")
                self.start_fetching()  # Restart the thread if it has stalled
                break  # Exit monitoring as the thread is restarted
        logger.info("Monitoring thread has exited.")


    def stop_fetching(self):
        """Stop the email fetching and monitoring processes gracefully."""
        
        # Signal both email fetching and monitoring threads to stop
        self.stop_thread.set()  # This should come first to notify both threads to stop
        
        # Check if the monitoring thread exists and is alive before attempting to join
        if hasattr(self, 'monitoring_thread') and self.monitoring_thread.is_alive():
            logger.info("Stopping fetching thread monitoring.")
            self.monitoring_thread.join(timeout=5)  # Wait for monitoring thread to finish
            if self.monitoring_thread.is_alive():
                logger.warning("Monitoring thread did not exit in time.")
            else:
                logger.info("Monitoring thread stopped successfully.")
        
        # Check if the fetching thread is alive before attempting to join
        if self.thread and self.thread.is_alive():
            logger.info("Stopping email fetching thread.")
            self.thread.join(timeout=10)  # Wait for the fetching thread to finish, with a timeout
            if self.thread.is_alive():
                logger.warning("Fetching thread did not exit in time, it may be stuck.")
            else:
                logger.info("eMail thread stopped successfully.")
    


if __name__ == "__main__":
    email_fetcher = EmailFetcher(
        "imap.server.com", 
        "your_email@example.com", 
        "password", 
        mark_as_seen=False, 
        interval=600,  
        ignore_file_types=["gif", "bmp"]
    )
    email_fetcher.start_fetching()  

    # Do other processing here

    # To stop the email fetching process:
    email_fetcher.stop_fetching()  