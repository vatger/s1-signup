from django import forms
from .models import Attendance, Comment, Session
from django.forms import modelformset_factory

class SessionAdminForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        airport_field = self.fields.get("airport")
        if airport_field is None:
            return

        current_airport = (
            self.instance.airport if not self.instance._state.adding else None
        )
        airport_field.choices = [
            (
                value,
                f"{label} (retired)" if value in Session.RETIRED_AIRPORTS else label,
            )
            for value, label in airport_field.choices
            if value not in Session.RETIRED_AIRPORTS or value == current_airport
        ]


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["attended"]
        widgets = {
            "attended": forms.Select(choices=Attendance.Status.choices),
        }


AttendanceFormSet = modelformset_factory(
    Attendance,
    form=AttendanceForm,
    extra=0,  # No extra empty forms
)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        exclude = ["user", "date_added", "author"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3}),
        }


class UserDetailForm(forms.Form):
    user_id = forms.CharField(
        max_length=7,
        label="User ID",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter User ID"}
        ),
    )
