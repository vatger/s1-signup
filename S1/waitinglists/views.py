import os
from datetime import datetime
from pathlib import Path

import requests
from connect.models import UserDetail
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.forms import modelformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from dotenv import load_dotenv

from .forms import AttendanceForm, CommentForm, UserDetailForm
from .helpers import (
    send_moodle_find_user,
    send_moodle_activity_completion,
    quiz_ids,
    send_forum_msg,
    can_upgrade,
    upgrade_and_add_to_roster,
    eud_header,
)
from .models import Attendance, Session, WaitingList, Module, Signup, QuizCompletion

load_dotenv()


def is_mentor(user):
    return user.groups.filter(name="Mentor").exists()


def module_2_completion(user, fetch=False):
    # Prepare a dictionary for storing results
    array = {}

    # Fetch all existing completions for the user
    completions = QuizCompletion.objects.filter(
        user=user, quiz_id__in=quiz_ids.values()
    )
    completion_dict = {comp.quiz_id: comp for comp in completions}

    for name, quiz_id in quiz_ids.items():
        # Check for existing completion
        if quiz_id not in completion_dict and fetch:
            res, time = send_moodle_activity_completion(user.username, quiz_id)
            if res:
                time = datetime.fromtimestamp(time)
                QuizCompletion.objects.create(
                    user=user, quiz_id=quiz_id, date_completed=time
                )
                # Update completion_dict to include the new completion
                completion_dict[quiz_id] = QuizCompletion(
                    user=user, quiz_id=quiz_id, date_completed=time
                )

        # Populate the result array
        if quiz_id in completion_dict:
            array[name] = [completion_dict[quiz_id].date_completed, True]
        else:
            array[name] = [None, False]

    return array, len([val for val in array.values() if val[1] == True]) == 4


def check_modules(user):
    try:
        mod3 = Module.objects.get(name="Module 3")
        mod4 = Module.objects.get(name="Module 4")
        wait3 = WaitingList.objects.get(user=user, module=mod3)
        wait4 = WaitingList.objects.get(user=user, module=mod4)
        if wait3.completed and wait4.completed:
            data = {
                "user_cid": user.username,
                "exam_id": 6,
                "instructor_cid": os.getenv("INSTRUCTOR_CID"),
            }
            requests.post(
                "https://core.vateud.net/api/facility/training/exams/assign",
                headers=eud_header,
                data=data,
            )
    except:
        pass


@login_required
def update_module_2(request):
    module_2_completion(request.user, fetch=True)
    return HttpResponseRedirect(reverse("index"))


@login_required
def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    user = request.user
    module_2_detail, module_2_completed = module_2_completion(user, fetch=False)
    is_ger = user.userdetail.subdivision == "GER"
    is_moodle_signed_up = send_moodle_find_user(user.username) != False
    waiting_for_modules = []

    module_list = Module.objects.all().order_by("name")
    if not module_2_completed:
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
        "module_2_detail": module_2_detail,
        "can_upgrade": can_upgrade(int(user.username)),
        "has_upgraded": user.userdetail.upgraded,
    }
    return HttpResponse(template.render(context, request))


@login_required
def waiting_list(request, module_id):
    try:
        waiting_list_entry = WaitingList.objects.get(
            user=request.user, module=Module.objects.get(id=module_id)
        )
        if not waiting_list_entry.completed:
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
    session_over = session.datetime < timezone.now()
    context = {
        "session": session,
        "attendances": attendances,
        "prefer_en": request.user.userdetail.en_preferred,
        "is_mentor": is_mentor(request.user),
        "authenticated": request.user.is_authenticated,
        "session_over": session_over,
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
                    check_modules(attendance.user)
                    if session.module.name == "Module 1":
                        if not os.path.exists("/opt/s1/S1/db/moodle-signup"):
                            os.makedirs("/opt/s1/S1/db/moodle-signup")
                        Path(
                            f"/opt/s1/S1/db/moodle-signup/{attendance.user.username}"
                        ).touch(exist_ok=True)
                elif attendance.attended == "ABS":
                    try:
                        waiting_list_entry = WaitingList.objects.get(
                            user=attendance.user, module=session.module
                        )
                        # waiting_list_entry.delete()
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
    if total_attendance < session.capacity and session.open_signup:
        attendance = Attendance.objects.update_or_create(
            user=request.user, session=session
        )
        send_forum_msg(
            request.user.username,
            "Confirmed Signup",
            f"""Your signup for the session {session} has been confirmed.
                        The session will be held on the VATGER Teamspeak. 
                        Please check beforehand if you can access the server.
                        More information can be found in the knowledge base.""",
            "S1 Centre",
            os.getenv("SITE_URL"),
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
    timeout_details = UserDetail.objects.filter(flagged_for_deletion=True)
    timeout_users = [detail.user for detail in timeout_details]
    list_len = {}
    for module in modules:
        list_len[module] = WaitingList.objects.filter(
            module=module, completed=False
        ).count()

    if request.method == "POST":
        form = UserDetailForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data["user_id"]
            # Check if the user exists
            if User.objects.filter(username=user_id).exists():
                # Redirect to the user_detail view
                return redirect(reverse("user_details", args=[user_id]))
            else:
                form.add_error("user_id", "User not found.")
    else:
        form = UserDetailForm()

    context = {
        "sessions": sessions,
        "prefer_en": request.user.userdetail.en_preferred,
        "authenticated": request.user.is_authenticated,
        "is_mentor": is_mentor(request.user),
        "modules": list_len,
        "timeout_users": timeout_users,
        "form": form,
    }
    template = loader.get_template("waitinglists/management.html")
    return HttpResponse(template.render(context, request))


@user_passes_test(is_mentor)
def user_detail(request, user_id):
    user = User.objects.get(username=user_id)
    mod2_quizzes, _ = module_2_completion(user, fetch=True)
    module_list = Module.objects.all().order_by("name")
    modules_completed = []
    for module in module_list:
        try:
            entry = WaitingList.objects.get(user=user, module=module)
            if entry.completed:
                modules_completed.append(True)
            else:
                modules_completed.append(False)
        except:
            modules_completed.append(False)
    comments = user.comments.all().order_by("-date_added")
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data["text"]
            author = request.user
            user.comments.create(text=text, author=author)
            return HttpResponseRedirect(reverse("user_details", args=[user_id]))
    else:
        form = CommentForm()

    context = {
        "user": user,
        "prefer_en": request.user.userdetail.en_preferred,
        "authenticated": request.user.is_authenticated,
        "is_mentor": is_mentor(request.user),
        "module_2_detail": mod2_quizzes,
        "modules_completed": modules_completed,
        "comments": comments,
        "form": form,
    }
    template = loader.get_template("waitinglists/user_detail.html")
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


@user_passes_test(is_mentor)
def past_sessions(request):
    sessions = Session.objects.filter(attendance_done=True).order_by("datetime")
    context = {
        "sessions": sessions,
        "prefer_en": request.user.userdetail.en_preferred,
        "is_mentor": is_mentor(request.user),
        "authenticated": request.user.is_authenticated,
    }
    template = loader.get_template("waitinglists/past_sessions.html")
    return HttpResponse(template.render(context, request))


@login_required
def upgrade(request):
    user = request.user
    if not can_upgrade(int(user.username)):
        return HttpResponseRedirect(reverse("index"))

    succ = upgrade_and_add_to_roster(int(user.username))
    if not succ:
        return HttpResponseRedirect(reverse("index"))
    user.userdetail.upgraded = True
    user.userdetail.save()
    return HttpResponseRedirect(reverse("index"))
