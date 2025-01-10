import os
from pathlib import Path

import requests
from cachetools import cached, TTLCache
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import modelformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from dotenv import load_dotenv

from .forms import AttendanceForm
from .helpers import send_moodle_find_user
from .models import Attendance, Session, WaitingList, Module, Signup

load_dotenv()


def check_course_completion(quiz_id: int, cid: int) -> bool:
    headers = {"Authorization": os.getenv("MOODLE_AUTH")}
    request = requests.get(
        f"{os.getenv('MOODLE_LINK')}/module_completed?module_id={quiz_id}&user_id={cid}",
        headers=headers,
    ).json()
    if request:
        completion_state = request[0]["completionstate"]
        if completion_state == 2:
            return True
    return False


def is_mentor(user):
    return user.groups.filter(name="Mentor").exists()


@cached(cache=TTLCache(maxsize=float("inf"), ttl=60 * 10))
def module_2_completed(user):
    basic = check_course_completion(1526, user.username)
    delivery = check_course_completion(1527, user.username)
    ground = check_course_completion(1525, user.username)
    tower = check_course_completion(1528, user.username)
    return basic and delivery and ground and tower


def check_modules(cid):
    # TODO: check if this is using the correct user ID
    try:
        mod3 = Module.objects.get(name="Module 3")
        mod4 = Module.objects.get(name="Module 4")
        wait3 = WaitingList.objects.get(user_id=cid, module=mod3)
        wait4 = WaitingList.objects.get(user_id=cid, module=mod4)
        if wait3.completed and wait4.completed:
            data = {
                "user_cid": cid,
                "exam_id": 6,
                "instructor_cid": os.getenv("INSTRUCTOR_CID"),
            }
            eud_header = {
                "X-API-KEY": os.getenv("CORE_API_KEY"),
                "Accept": "application/json",
                "User-Agent": "VATGER",
            }
            requests.post(
                "https://core.vateud.net/api/facility/training/exams/assign",
                headers=eud_header,
                data=data,
            )
    except:
        pass


@login_required
def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    user = request.user
    user.userdetail.module_2_completed = (
        user.userdetail.module_2_completed or module_2_completed(user)
    )
    is_ger = user.userdetail.subdivision == "GER"
    is_moodle_signed_up = send_moodle_find_user(user.username)
    waiting_for_modules = []

    module_list = Module.objects.all().order_by("name")
    if not user.userdetail.module_2_completed:
        module_list = module_list[:1]

    modules = {}
    for module in module_list:
        try:
            entry = WaitingList.objects.get(user=user, module=module)
            if not entry.completed:
                waiting_for_modules.append(entry.module.id)
                waiting_ahead = WaitingList.objects.filter(
                    module=entry.module,
                    completed=False,
                    date_added__lt=entry.date_added,
                ).count()
                can_renew = entry.expiry_date - timezone.now() < timezone.timedelta(
                    days=31
                )
                modules[module.name] = (
                    module.id,
                    True,
                    entry.completed,
                    entry.expiry_date,
                    waiting_ahead,
                    can_renew,
                )
            else:
                modules[module.name] = (
                    module.id,
                    True,
                    entry.completed,
                    entry.date_completed,
                    0,
                    False,
                )
        except:
            modules[module.name] = (module.id, False, False, False, 0, False)

    # Filter sessions that are not yet started
    sessions = Session.objects.filter(
        datetime__gt=timezone.now(), module__id__in=waiting_for_modules
    ).order_by("datetime")
    free_spots = {}
    for session in sessions:
        if session.open_signup:
            free_spot = (
                session.capacity - Attendance.objects.filter(session=session).count()
            )
            free_spots[session.id] = free_spot
    template = loader.get_template("waitinglists/index.html")

    signups = Signup.objects.filter(user=user)
    signups = [signup.session.id for signup in signups]

    # Get user attendances
    attendances = Attendance.objects.filter(
        user=user, session__datetime__gt=timezone.now()
    ).order_by("session__datetime")
    attendend_session_ids = [attendance.session.id for attendance in attendances]

    context = {
        "sessions": sessions,
        "is_ger": is_ger,
        "prefer_en": user.userdetail.en_preferred,
        "signups": signups,
        "authenticated": request.user.is_authenticated,
        "modules": modules,
        "free_spots": free_spots,
        "attendances": attendances,
        "attended_session_ids": attendend_session_ids,
        "is_mentor": is_mentor(request.user),
        "is_moodle_signed_up": is_moodle_signed_up,
    }
    return HttpResponse(template.render(context, request))


@login_required
def waiting_list(request, module_id):
    try:
        waiting_list_entry = WaitingList.objects.get(
            user=request.user, module=Module.objects.get(id=module_id)
        )
        waiting_list_entry.delete()
    except:
        expiry_date = timezone.now() + timezone.timedelta(days=63)
        expiry_date = expiry_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        entry = WaitingList(
            user=request.user,
            module=Module.objects.get(id=module_id),
            expiry_date=expiry_date,
        )
        entry.save()

    return HttpResponseRedirect(reverse("index"))


@login_required
def signup(request, session_id):
    # Create new signup entry, but check if user is already signed up
    signup = Signup.objects.filter(
        user=request.user,
        session=Session.objects.get(id=session_id),
    )
    if signup:
        signup.delete()
        return HttpResponseRedirect(reverse("index"))
    session = Session.objects.get(id=session_id)
    waiting_list_entry = WaitingList.objects.get(
        user=request.user, module=session.module
    )
    new = Signup(
        user=request.user,
        session=session,
        waiting_list=waiting_list_entry,
    )
    new.save()
    return HttpResponseRedirect(reverse("index"))


@user_passes_test(is_mentor)
def session_detail(request, session_id):
    session = Session.objects.get(id=session_id)
    attendances = Attendance.objects.filter(session=session)
    context = {
        "session": session,
        "attendances": attendances,
        "prefer_en": request.user.userdetail.en_preferred,
        "is_mentor": is_mentor(request.user),
        "authenticated": request.user.is_authenticated,
    }
    return render(request, "waitinglists/Session.html", context)


@user_passes_test(is_mentor)
def update_attendance(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    attendance_queryset = Attendance.objects.filter(session=session)

    AttendanceFormSet = modelformset_factory(Attendance, form=AttendanceForm, extra=0)

    if request.method == "POST":
        formset = AttendanceFormSet(request.POST, queryset=attendance_queryset)
        if formset.is_valid():
            formset.save()
            # Logic to update waiting list
            attendances = Attendance.objects.filter(session=session)
            for attendance in attendances:
                if attendance.attended == "ATT":
                    try:
                        waiting_list_entry = WaitingList.objects.get(
                            user=attendance.user, module=session.module
                        )
                        waiting_list_entry.completed = True
                        waiting_list_entry.date_completed = timezone.now()
                        waiting_list_entry.save()
                    except:
                        pass
                    check_modules(attendance.user.id)
                    if session.module.name == "Module 1":
                        if not os.path.exists("opt/s1/S1/db/moodle-signup"):
                            os.makedirs("opt/s1/S1/db/moodle-signup")
                        Path(f"opt/s1/moodle-signup/{attendance.user.username}").touch(
                            exist_ok=True
                        )
                        # enrol_and_check_overrides(attendance.user.username)
                elif attendance.attended == "ABS":
                    try:
                        waiting_list_entry = WaitingList.objects.get(
                            user=attendance.user, module=session.module
                        )
                        waiting_list_entry.delete()
                    except:
                        pass
            session.attendance_done = True
            session.save()
            return redirect("session_detail", session_id=session.id)
    else:
        formset = AttendanceFormSet(queryset=attendance_queryset)

    return render(
        request,
        "waitinglists/update_attendance.html",
        {
            "session": session,
            "formset": formset,
            "prefer_en": request.user.userdetail.en_preferred,
            "authenticated": request.user.is_authenticated,
            "is_mentor": is_mentor(request.user),
        },
    )


@login_required
def update_preferred_language(request):
    user = request.user
    user.userdetail.en_preferred = not user.userdetail.en_preferred
    user.userdetail.save()
    next_url = request.META.get("HTTP_REFERER", "/")
    return redirect(next_url)


@login_required
def renew_waiting_list(request, module_id):
    try:
        entry = WaitingList.objects.get(
            user=request.user, module=Module.objects.get(id=module_id)
        )
        if not entry.expiry_date - timezone.now() < timezone.timedelta(days=31):
            return HttpResponseRedirect(reverse("index"))
        entry.expiry_date = entry.expiry_date + timezone.timedelta(days=31)
        entry.expiry_date = entry.expiry_date.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        entry.save()
    except:
        pass
    return HttpResponseRedirect(reverse("index"))


@login_required
def open_signup(request, session_id):
    session = Session.objects.get(id=session_id)
    total_attendance = Attendance.objects.filter(session=session).count()
    if total_attendance < session.capacity:
        attendance = Attendance.objects.update_or_create(
            user=request.user, session=session
        )
    return HttpResponseRedirect(reverse("index"))


@login_required
def cancel_attendance(request, session_id):
    session = Session.objects.get(id=session_id)
    attendance = Attendance.objects.get(user=request.user, session=session)
    attendance.delete()
    return HttpResponseRedirect(reverse("index"))


@user_passes_test(is_mentor)
def management(request):
    sessions = Session.objects.filter(attendance_done=False).order_by("datetime")
    modules = Module.objects.all().order_by("name")
    context = {
        "sessions": sessions,
        "prefer_en": request.user.userdetail.en_preferred,
        "authenticated": request.user.is_authenticated,
        "is_mentor": is_mentor(request.user),
        "modules": modules,
    }
    template = loader.get_template("waitinglists/management.html")
    return HttpResponse(template.render(context, request))


@user_passes_test(is_mentor)
def total_waiting_list(request, module_id):
    waiting_list_entries = WaitingList.objects.filter(
        module=Module.objects.get(id=module_id), completed=False
    ).order_by("date_added")
    context = {
        "waiting_list_entries": waiting_list_entries,
        "prefer_en": request.user.userdetail.en_preferred,
        "is_mentor": is_mentor(request.user),
        "authenticated": request.user.is_authenticated,
    }
    template = loader.get_template("waitinglists/waitinglist.html")
    return HttpResponse(template.render(context, request))
