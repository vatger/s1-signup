import requests
import os
from dotenv import load_dotenv

load_dotenv()


def send_forum_msg(id: int, title: str, msg: str, link_text: str, link_url: str):
    data = {
        "title": title,
        "message": msg,
        "source_name": "VATGER ATD",
        "link_text": link_text,
        "link_url": link_url,
    }
    header = {"Authorization": f"Token {os.getenv("VATGER_API_KEY")}"}
    r = requests.post(
        f"https://vatsim-germany.org/api/user/{id}/send_notification",
        data=data,
        headers=header,
    )
    return r.json()
