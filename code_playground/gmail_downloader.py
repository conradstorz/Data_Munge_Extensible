"""Gmail monitor program and attachment downloader

requirements:
    pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

import os
import base64
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """
    Authenticates the user using OAuth 2.0 and returns the Gmail API service.

    Returns:
        googleapiclient.discovery.Resource: Authorized Gmail API service instance.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    print("Authenticated successfully.")
    return build('gmail', 'v1', credentials=creds)

def search_emails_with_attachments(service):
    """
    Searches for emails with attachments.

    Args:
        service (googleapiclient.discovery.Resource): Authorized Gmail API service instance.

    Returns:
        list: List of messages with attachments.
    """
    print("Searching for emails with attachments...")
    results = service.users().messages().list(userId='me', q="has:attachment").execute()
    messages = results.get('messages', [])
    print(f"Search complete. Found {len(messages)} emails with attachments.")
    return messages

def download_attachments(service, message_id, store_dir):
    """
    Downloads attachments from a specific email.

    Args:
        service (googleapiclient.discovery.Resource): Authorized Gmail API service instance.
        message_id (str): ID of the email message.
        store_dir (str): Directory to store the downloaded attachments.

    Returns:
        None
    """
    print(f"Downloading attachments from message ID: {message_id}")
    message = service.users().messages().get(userId='me', id=message_id).execute()
    
    if 'parts' in message['payload']:
        for part in message['payload']['parts']:
            if part['filename']:
                print(f"Found attachment: {part['filename']}")
                if 'data' in part['body']:
                    data = part['body']['data']
                else:
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(userId='me', messageId=message_id, id=att_id).execute()
                    data = att['data']
                
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                path = os.path.join(store_dir, part['filename'])

                with open(path, 'wb') as f:
                    f.write(file_data)
                print(f'Saved attachment: {path}')
    else:
        print("No attachments found in this email.")

def main():
    """
    Main function to run the Gmail Attachment Downloader script.

    Returns:
        None
    """
    print("Starting Gmail Attachment Downloader Script...")
    service = authenticate_gmail()
    store_dir = 'attachments'
    
    if not os.path.exists(store_dir):
        os.makedirs(store_dir)
        print(f"Created directory for attachments: {store_dir}")
    else:
        print(f"Using existing directory for attachments: {store_dir}")

    while True:
        try:
            print("Checking for new emails with attachments...")
            messages = search_emails_with_attachments(service)
            if not messages:
                print('No new messages with attachments.')
            else:
                for message in messages:
                    print(f"Processing message ID: {message['id']}")
                    download_attachments(service, message['id'], store_dir)
            print("Waiting for 60 seconds before checking again...")
            time.sleep(60)  # Check every minute
        except HttpError as error:
            print(f'An error occurred: {error}')
            print("Waiting for 60 seconds before retrying...")
            time.sleep(60)

if __name__ == '__main__':
    main()