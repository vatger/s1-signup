import os

import requests
from cachetools import TTLCache, cached
from dotenv import load_dotenv
from datetime import datetime, timezone

from theoryroster.models import RosterEntry


load_dotenv()

quiz_ids = {
    "Basics": 1526,
    "Delivery": 1527,
    "Ground": 1525,
    "Tower": 1528,
}


eud_header = {
    "X-API-KEY": os.getenv("CORE_API_KEY"),
    "Accept": "application/json",
    "User-Agent": "VATGER",
}


def send_forum_msg(id: int, title: str, msg: str, link_text: str, link_url: str, mail: bool = False) -> any:
    via = "board.ping"
    if mail:
        via += ",mail"
    data = {
        "title": title,
        "message": msg,
        "source_name": "VATGER ATD",
        "link_text": link_text,
        "link_url": link_url,
        "via": "board.ping",
    }
    
    header = {"Authorization": f"Token {os.getenv("VATGER_API_KEY")}"}
    r = requests.post(
        f"http://vatsim-germany.org/api/user/{id}/send_notification",
        data=data,
        headers=header,
    )
    return r.json()

def send_mail(id:int, title:str, msg:str, link_text:str, link_url:str) -> any:
    data = {
        "title": title,
        "message": msg,
        "source_name": "VATGER ATD",
        "link_text": link_text,
        "link_url": link_url,
        "via": "mail",
    }
    header = {"Authorization": f"Token {os.getenv("VATGER_API_KEY")}"}
    r = requests.post(
        f"http://vatsim-germany.org/api/user/{id}/send_notification",
        data=data,
        headers=header,
    )
    return r.json()

def generate_signup_confirmation_msg(session: Session, Mail: bool) -> str:
    if Mail:
        kb_link = "<a href='https://knowledgebase.vatsim-germany.org'>knowledge base</a>"
    else:
        kb_link = "[URL='https://knowledgebase.vatsim-germany.org']knowledge base[/URL]"


    msg = (
        f"Your signup for the session {session} has been confirmed.\n"
        "The session will be held on the VATGER Teamspeak. Please check beforehand if you can access the server.\n"
        f"More information can be found in the {kb_link}."
    )

    if session.module.name == 'Module 4' and session.airport:
        match session.airport:
            case 'EDDW':
                sop_url = "https://knowledgebase.vatsim-germany.org/books/sops-fir-bremen/chapter/eddw-bremen-airport"
                pack_url = "https://files.aero-nav.com/EDWW"
                pack_name = "EDWW Full-Package"
            case 'EDDC':
                sop_url = "https://knowledgebase.vatsim-germany.org/books/sops-fir-munchen/chapter/eddc-dresden-airport"
                pack_url = "https://files.aero-nav.com/EDMM"
                pack_name = "EDMM Full-Package"
            case 'EDDG':
                sop_url = "https://knowledgebase.vatsim-germany.org/books/sops-fir-langen/chapter/eddg-munsterosnabruck-airport"
                pack_url = "https://files.aero-nav.com/EDGG"
                pack_name = "EDGG Full_Package"
            case _:
                sop_url = ""
                pack_url = "https://files.aero-nav.com/EDXX"
                pack_name = "appropriate Package"

        if Mail:
            msg += (
                "\n\n"
                f"As part of the training, a simulation of air traffic control in "
                f"<a href='{sop_url}'>{session.get_airport_display()}</a> is carried out in Eurscope."
                f" This requires the <a href='{pack_url}'>{pack_name}</a> to be set up."
                f" Instructions on how to install Euroscope can be found in the <a href='https://knowledgebase.vatsim-germany.org/books/atc-software'>knowledge base</a>."
            )
        else:
            msg += (
                "\n\n"
                f"As part of the training, a simulation of air traffic control in "
                f"[URL='{sop_url}']{session.get_airport_display()}[/URL] is carried out in Eurscope."
                f" This requires the [URL='{pack_url}']{pack_name}[/URL] to be set up."
                f" Instructions on how to install Euroscope can be found in the [URL='https://knowledgebase.vatsim-germany.org/books/atc-software']knowledge base[/URL]."
            )

    return msg


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
    )
    try:
        result = r.json()
    except:
        print(f"Error decoding json with user id {user_id}")
        print(r)
        return False
    try:
        return result["id"]
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
            and datetime.strptime(test["expiry"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(
                tzinfo=timezone.utc
            )
            > datetime.now(timezone.utc)
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
            data={"new_rating": 2, "instructor_cid": os.getenv("INSTRUCTOR_CID")},
        ).json()["success"]
        roster = requests.post(
            f"https://core.vateud.net/api/facility/roster/{vatsim_id}",
            headers=eud_header,
        ).json()["success"]
        tr_entry = RosterEntry(cid=int(vatsim_id))
        tr_entry.save()
        return upgrade and roster
    except:
        return False
