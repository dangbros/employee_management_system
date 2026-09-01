from django import forms


class LeaveRequestForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
    )
