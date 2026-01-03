import os

from dotenv import load_dotenv

load_dotenv()


def get_server_url():
    return os.getenv("SERVER_URL")