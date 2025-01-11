from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:module_id>/join", views.waiting_list, name="waiting_list"),
    path("<int:session_id>/signup", views.signup, name="signup"),
    path("<int:session_id>/detail", views.session_detail, name="session_detail"),
    path(
        "<int:session_id>/attendance/",
        views.update_attendance,
        name="update_attendance",
    ),
    path("lang", views.update_preferred_language, name="change_language"),
    path("<int:module_id>/renew", views.renew_waiting_list, name="renew_waiting_list"),
    path("<int:session_id>/open_signup", views.open_signup, name="open_signup"),
    path(
        "<int:session_id>/cancel_attendance",
        views.cancel_attendance,
        name="cancel_attendance",
    ),
    path("management", views.management, name="management"),
    path(
        "<int:module_id>/waiting_list",
        views.total_waiting_list,
        name="total_waiting_list",
    ),
    path("update_module", views.update_module_2, name="update_module"),
    path("<int:user_id>/details", views.user_detail, name="user_details"),
]
