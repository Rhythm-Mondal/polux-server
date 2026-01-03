import os
import shutil
from uuid import UUID

from dotenv import load_dotenv

load_dotenv()


def get_server_url():
    return os.getenv("SERVER_URL")


def get_local_storage_upload_info(space_id: UUID, storage_id: UUID, name: str):
    ext = name.split(".", maxsplit=1)
    name = storage_id.hex
    if ext:
        name += f".{ext}"
    return {
        "url": f"{get_server_url()}/{space_id}/blobs",
        "fields": {
            "storage_id": storage_id,
            "key": f"~/PoluxContentStorage/space_id={space_id}/{name}",
        },
    }


def save_file_local(*, key: str, fileobj):
    path = os.path.join(key)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "wb") as f:
        shutil.copyfileobj(fileobj, f)
