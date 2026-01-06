import os, json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

FILE_NAME = "result.jpg"

def main():
    sa_json = os.environ["GDRIVE_SA_JSON"]
    folder_id = os.environ["GDRIVE_FOLDER_ID"]

    info = json.loads(sa_json)
    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    drive = build("drive", "v3", credentials=creds)

    # 同名があれば update（上書き）、なければ create
    q = f"name='{FILE_NAME}' and '{folder_id}' in parents and trashed=false"
    res = drive.files().list(q=q, fields="files(id,name)").execute()
    files = res.get("files", [])

    media = MediaFileUpload(FILE_NAME, mimetype="image/jpeg", resumable=True)

    if files:
        file_id = files[0]["id"]
        drive.files().update(fileId=file_id, media_body=media).execute()
        print("Updated:", file_id)
    else:
        meta = {"name": FILE_NAME, "parents": [folder_id]}
        created = drive.files().create(body=meta, media_body=media, fields="id").execute()
        print("Created:", created["id"])

if __name__ == "__main__":
    main()
