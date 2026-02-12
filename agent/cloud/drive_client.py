from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pathlib import Path


CREDENTIALS_DIR = Path("agent/credentials")
CLIENT_SECRET_FILE = CREDENTIALS_DIR / "credentials.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"


class DriveClient:
    def __init__(self):
        self.gauth = GoogleAuth()

        self.gauth.LoadClientConfigFile(str(CLIENT_SECRET_FILE))

        # Try loading saved credentials
        if TOKEN_FILE.exists():
            self.gauth.LoadCredentialsFile(str(TOKEN_FILE))

        if self.gauth.credentials is None:
            # First-time login
            self.gauth.LocalWebserverAuth()
        elif self.gauth.access_token_expired:
            self.gauth.Refresh()
        else:
            self.gauth.Authorize()

        # Save credentials for next run
        self.gauth.SaveCredentialsFile(str(TOKEN_FILE))

        self.drive = GoogleDrive(self.gauth)

    def upload_file(self, file_path: Path) -> str:
        file = self.drive.CreateFile({"title": file_path.name})
        file.SetContentFile(str(file_path))
        file.Upload()
        return file["id"]
