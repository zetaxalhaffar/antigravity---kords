from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import io
import pickle
import os

# Scope for reading and writing files
SCOPES = ['https://www.googleapis.com/auth/drive']

class DriveClient:
    def __init__(self, credentials_path='credentials.json', token_path='token.pickle'):
        self.creds = None
        self.service = None
        self.credentials_path = credentials_path
        self.token_path = token_path
        
    def authenticate(self):
        """Authenticates the user using OAuth2."""
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)
                
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"Could not find {self.credentials_path}. You receive this file from Google Cloud Console.")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('drive', 'v3', credentials=self.creds)

    def list_files_in_folder(self, folder_id):
        """Lists files in a specific Google Drive folder."""
        results = self.service.files().list(
            q=f"'{folder_id}' in parents and trashed = false and name contains '.xlsx'",
            fields="nextPageToken, files(id, name)"
        ).execute()
        return results.get('files', [])

    def download_file(self, file_id, local_path):
        """Downloads a file from Drive to local path."""
        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(local_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        print(f"Downloaded {local_path}")

    def upload_file(self, local_path, folder_id, file_name=None):
        """Uploads a file to a specific Drive folder."""
        if not file_name:
            file_name = os.path.basename(local_path)
            
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(local_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Uploaded {file_name} (File ID: {file.get('id')})")
        return file.get('id')
