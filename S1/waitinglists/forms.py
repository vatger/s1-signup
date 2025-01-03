from django import forms
from .models import Attendance
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
