import os

import requests
from cachetools import TTLCache, cached
from dotenv import load_dotenv

from .views import eud_header

load_dotenv()

quiz_ids = {
    "Basics": 1526,
    "Delivery": 1527,
    "Ground": 1525,
    "Tower": 1528,
}


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


@cached(cache=TTLCache(maxsize=float("inf"), ttl=60 * 10))
def send_moodle_activity_completion(
    user_id: int, course_module_id: int
) -> tuple[bool, float]:

    header = {"Authorization": f"Token {os.getenv("VATGER_API_KEY")}"}
    r = requests.get(
        f"http://vatsim-germany.org/api/moodle/activity/{course_module_id}/user/{user_id}/completion",
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


@cached(cache=TTLCache(maxsize=float("inf"), ttl=60 * 10))
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


def enrol_and_check_overrides(vatsim_id: int):
    # Enrols user in Module 2 and updates overrides accordingly.
    res = send_moodle_enrol_user(vatsim_id, 86)
    for id in quiz_ids.values():
        attempts = send_moodle_count_attempts(vatsim_id, id)
        if attempts > 0:
            send_moodle_override_attempts(vatsim_id, id, attempts + 1)


cache = TTLCache(maxsize=float("inf"), ttl=60 * 10)


def check_vatsim_api_for_upgrade(vatsim_id: int) -> bool:
    if vatsim_id in cache:
        return cache[vatsim_id]

    try:
        r = requests.get(f"https://api.vatsim.net/v2/members/{vatsim_id}/").json()
        result = r["rating"] == 1 and r["subdivision_id"] == "GER"
        cache[vatsim_id] = result  # Only cache successful results
        return result
    except:
        return False


def can_upgrade(vatsim_id: int) -> bool:
    try:
        res = requests.get(
            f"https://core.vateud.net/api/facility/user/{vatsim_id}/exams",
            headers=eud_header,
        ).json()["data"]["results"]
        filtered = [
            test
            for test in res
            if test["exam_id"] == 6
            and test["passed"]  # Magic number 6 is VATEUD Core S1 Theory Test id
        ]
    except:
        filtered = []
    return check_vatsim_api_for_upgrade(vatsim_id) and bool(filtered)


def upgrade_and_add_to_roster(vatsim_id: int) -> bool:
    if not can_upgrade(vatsim_id):
        return False
    try:
        upgrade = requests.post(
            f"https://core.vateud.net/api/facility/user/{vatsim_id}/upgrade",
            headers=eud_header,
        ).json()["success"]
        roster = requests.post(
            f"https://core.vateud.net/api/facility/roster/{vatsim_id}",
            headers=eud_header,
        ).json()["success"]
        return upgrade and roster
    except:
        return False
