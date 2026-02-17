"""
DriveClient (Production Version)
---------------------------------
Non-interactive Google Drive client.
Requires token.json generated beforehand.
"""

from pathlib import Path
from typing import Optional
from pydrive2.auth import GoogleAuth, RefreshError
from pydrive2.drive import GoogleDrive


CREDENTIALS_DIR = Path("agent/credentials")
CLIENT_SECRET_FILE = CREDENTIALS_DIR / "credentials.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"


class DriveClient:
    def __init__(self, logger):
        self.logger = logger
        self.drive: Optional[GoogleDrive] = None

        try:
            self._authenticate()
            self.logger.info("Drive client initialized successfully.")
        except Exception as e:
            self.logger.error(
                "Drive initialization failed.",
                extra={"metadata": {"error": str(e)}},
            )
            self.drive = None

    def _authenticate(self):
        if not CLIENT_SECRET_FILE.exists():
            raise FileNotFoundError(f"Missing credentials.json at {CLIENT_SECRET_FILE}")

        if not TOKEN_FILE.exists():
            raise Exception(
                "token.json missing. Run setup_drive_auth.py once before starting agent."
            )

        gauth = GoogleAuth()
        gauth.settings["client_config_file"] = str(CLIENT_SECRET_FILE)

        # Load saved token
        gauth.LoadCredentialsFile(str(TOKEN_FILE))

        if gauth.credentials is None:
            raise Exception("Invalid token.json. Re-run setup_drive_auth.py")

        # Silent refresh if needed
        if gauth.access_token_expired:
            try:
                self.logger.info("Refreshing Drive token...")
                gauth.Refresh()
            except RefreshError:
                raise Exception("Token refresh failed. Re-run setup_drive_auth.py")

        gauth.Authorize()
        gauth.SaveCredentialsFile(str(TOKEN_FILE))

        self.drive = GoogleDrive(gauth)

    def upload_file(self, file_path: Path, subfolder_name: Optional[str] = None) -> Optional[str]:
        if not self.drive:
            self.logger.warning("Drive unavailable. Upload skipped.")
            return None

        if not file_path.exists():
            self.logger.error(f"Upload failed. File missing: {file_path}")
            return None

        try:
            parent_id = None
            if subfolder_name:
                parent_id = self._get_or_create_folder(subfolder_name)

            metadata = {"title": file_path.name}
            if parent_id:
                metadata["parents"] = [{"id": parent_id}]

            drive_file = self.drive.CreateFile(metadata)
            drive_file.SetContentFile(str(file_path))
            drive_file.Upload()

            file_id = drive_file["id"]

            self.logger.info(
                "Drive upload successful",
                extra={"metadata": {"drive_file_id": file_id}},
            )

            return file_id

        except Exception as e:
            self.logger.error(
                "Drive upload failed.",
                extra={"metadata": {"error": str(e)}},
            )
            return None

    def _get_or_create_folder(self, folder_name: str) -> str:
        query = (
            f"title='{folder_name}' "
            "and mimeType='application/vnd.google-apps.folder' "
            "and trashed=false"
        )

        file_list = self.drive.ListFile({"q": query}).GetList()

        if file_list:
            return file_list[0]["id"]

        folder_metadata = {
            "title": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }

        folder = self.drive.CreateFile(folder_metadata)
        folder.Upload()
        return folder["id"]
