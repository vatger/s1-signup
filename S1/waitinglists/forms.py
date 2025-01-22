from django import forms
from .models import Attendance, Comment
from django.forms import modelformset_factory


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


class CommentForm(forms.Form):
    class Meta:
        model = Comment
        exclude = ["user", "date_added", "author"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3}),
        }
