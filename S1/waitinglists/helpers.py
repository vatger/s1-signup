import requests
import os
from dotenv import load_dotenv

load_dotenv()

quiz_ids = [1525, 1526, 1527, 1528]


def send_forum_msg(id: int, title: str, msg: str, link_text: str, link_url: str) -> any:
    data = {
        "title": title,
        "message": msg,
        "source_name": "VATGER ATD",
        "link_text": link_text,
        "link_url": link_url,
    }
    header = {"Authorization": f"Token {os.getenv("VATGER_API_KEY")}"}
    r = requests.post(
        f"http://vatsim-germany.org/api/user/{id}/send_notification",
        data=data,
        headers=header,
    )
    return r.json()


def send_moodle_activity_completion(
    user_id: int, course_module_id: int
) -> tuple[bool, float]:

    header = {"Authorization": f"Token {os.getenv("VATGER_API_KEY")}"}
    r = requests.get(
        f"http://vatsim-germany.org/api/moodle/quiz/{course_module_id}/user/{user_id}/results",
        headers=header,
    ).json()
    try:
        return r["isoverallcomplete"], r["timecompleted"]
    except:
        return False, 0


def send_moodle_enrol_user(user_id: int, course_id: int) -> bool:
    header = {"Authorization": f"Token {os.getenv("VATGER_API_KEY")}"}
    r = requests.get(
        f"http://vatsim-germany.org/api/moodle/course/{course_id}/user/{user_id}/enrol",
        headers=header,
    ).json()
    try:
        return r
    except:
        return False


def send_moodle_find_user(user_id: int) -> bool:
    header = {"Authorization": f"Token {os.getenv("VATGER_API_KEY")}"}
    r = requests.get(
        f"http://vatsim-germany.org/api/moodle/user/{user_id}",
        headers=header,
    ).json()
    try:
        return r["id"]
    except:
        return False


def send_moodle_count_attempts(user_id: int, course_module_id: int) -> int:
    header = {"Authorization": f"Token {os.getenv("VATGER_API_KEY")}"}
    r = requests.get(
        f"http://vatsim-germany.org/api/moodle/quiz/{course_module_id}/user/{user_id}/attempts",
        headers=header,
    ).json()
    try:
        return len(r)
    except:
        return 0


def send_moodle_override_attempts(
    user_id: int, course_module_id: int, attempts: int
) -> bool:
    header = {"Authorization": f"Token {os.getenv("VATGER_API_KEY")}"}
    r = requests.get(
        f"http://vatsim-germany.org/api/moodle/quiz/{course_module_id}/user/{user_id}/override/attempts/{attempts}",
        headers=header,
    ).json()
    try:
        return r
    except:
        return False


async def enrol_and_check_overrides(vatsim_id: int):
    # Enrols user in Module 2 and updates overrides accordingly.
    res = send_moodle_enrol_user(vatsim_id, 86)
    for id in quiz_ids:
        attempts = send_moodle_count_attempts(vatsim_id, id)
        if attempts > 0:
            send_moodle_override_attempts(vatsim_id, id, attempts + 1)
