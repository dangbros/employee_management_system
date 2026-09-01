from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

from .models import User


class RegistrationForm(UserCreationForm):
    """Self-service registration. Role is deliberately NOT exposed: everyone
    who registers becomes an employee; HR accounts are provisioned by admins.
    """

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("employee_id", "email", "first_name", "last_name", "department")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_employee_id(self):
        value = self.cleaned_data["employee_id"].strip().upper()
        if not value.isalnum():
            raise forms.ValidationError("Employee ID may only contain letters and digits.")
        if User.objects.filter(employee_id__iexact=value).exists():
            raise forms.ValidationError("An account with this employee ID already exists.")
        return value

    def clean_email(self):
        value = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return value

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["employee_id"]
        user.role = User.Role.EMPLOYEE  # never trusted from the client
        if commit:
            user.save()
        return user


class BootstrapAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Employee ID"
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class BootstrapPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class BootstrapSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
