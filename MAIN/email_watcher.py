import imaplib
import email
from email.header import decode_header
import os
from threading import Timer
from loguru import logger

class EmailAttachmentDownloader:
    def __init__(self, email_user, email_password, download_folder, interval=300):
        self.email_user = email_user
        self.email_password = email_password
        self.download_folder = download_folder
        self.interval = interval  # Time interval in seconds
        self.timer = None

    def download_attachments(self):
        try:
            # Connect to the server
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email_user, self.email_password)
            mail.select("inbox")

            # Search for all emails with attachments
            result, data = mail.search(None, '(HASATTACHMENT)')
            for num in data[0].split():
                result, data = mail.fetch(num, '(RFC822)')
                msg = email.message_from_bytes(data[0][1])

                # Iterate over email parts
                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                        continue

                    filename = part.get_filename()
                    if filename:
                        filepath = os.path.join(self.download_folder, filename)
                        with open(filepath, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        logger.info(f"Downloaded: {filename}")

            mail.logout()
        except Exception as e:
            logger.error(f"Error downloading attachments: {e}")

    def check_for_attachments(self):
        logger.info("Checking for new email attachments...")
        self.download_attachments()
        self.timer = Timer(self.interval, self.check_for_attachments)
        self.timer.start()

    def start(self):
        self.check_for_attachments()

    def stop(self):
        if self.timer is not None:
            self.timer.cancel()
