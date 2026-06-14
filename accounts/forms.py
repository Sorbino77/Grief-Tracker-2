"""Account-management forms used by the in-app admin pages."""

from __future__ import annotations

from allauth.account.forms import LoginForm as AllauthLoginForm
from allauth.account.forms import SignupForm as AllauthSignupForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from shiptrack.formhelpers import BootstrapFormMixin

from .models import AccessibilityPreferences, Role, User


class StyledLoginForm(BootstrapFormMixin, AllauthLoginForm):
    """Allauth login form with Bootstrap classes applied to every widget."""


class StyledSignupForm(BootstrapFormMixin, AllauthSignupForm):
    """Allauth signup form with Bootstrap classes applied to every widget."""


class UserCreateForm(BootstrapFormMixin, UserCreationForm):
    """Admin-side 'invite a teammate' form.

    Uses Django's ``UserCreationForm`` as the base so we get the standard
    password validators (12-char min, common-password blocklist, etc.) for
    free, then adds the email + role fields and enforces email uniqueness
    and a strong password explicitly (defence in depth — the model already
    has ``unique=True`` on email).
    """

    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Role.choices, initial=Role.VIEWER)

    class Meta:
        model = User
        fields = ("username", "email", "role")

    def clean_email(self) -> str:
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_username(self) -> str:
        username = (self.cleaned_data.get("username") or "").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username

    def _post_clean(self) -> None:
        # Run Django's password validators against the user instance so that
        # UserAttributeSimilarityValidator can compare against the username.
        super()._post_clean()  # type: ignore[misc]
        password = self.cleaned_data.get("password2")
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as e:
                self.add_error("password2", e)

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]
        # Mirror admin's behaviour for staff/superuser: only Admins get is_staff
        # so they can reach Django admin if they need it. Editors/viewers
        # never get is_staff or is_superuser.
        user.is_staff = user.role == Role.ADMIN
        user.is_superuser = False
        if commit:
            user.save()
        return user


class AccessibilityPreferencesForm(BootstrapFormMixin, forms.ModelForm):
    """Gaming-style accessibility settings form."""

    class Meta:
        model = AccessibilityPreferences
        fields = [
            "high_contrast_mode",
            "dyslexia_friendly_font",
            "font_size",
            "colorblind_mode",
            "reduced_motion",
            "large_touch_targets",
            "keyboard_navigation_hints",
            "simplified_layout",
            "reading_guide",
            "captions",
            "screen_reader_mode",
        ]
        widgets = {
            "high_contrast_mode": forms.CheckboxInput(
                attrs={"class": "form-check-input", "title": "Increase color contrast for better visibility"}
            ),
            "dyslexia_friendly_font": forms.CheckboxInput(
                attrs={"class": "form-check-input", "title": "Use dyslexia-friendly font"}
            ),
            "font_size": forms.RadioSelect(attrs={"class": "form-check-input"}),
            "colorblind_mode": forms.RadioSelect(attrs={"class": "form-check-input"}),
            "reduced_motion": forms.CheckboxInput(
                attrs={"class": "form-check-input", "title": "Reduce animations and transitions"}
            ),
            "large_touch_targets": forms.CheckboxInput(
                attrs={"class": "form-check-input", "title": "Increase button and interactive element sizes"}
            ),
            "keyboard_navigation_hints": forms.CheckboxInput(
                attrs={"class": "form-check-input", "title": "Show keyboard navigation shortcuts"}
            ),
            "simplified_layout": forms.CheckboxInput(
                attrs={"class": "form-check-input", "title": "Hide advanced features"}
            ),
            "reading_guide": forms.CheckboxInput(
                attrs={"class": "form-check-input", "title": "Highlight current line with reading guide"}
            ),
            "captions": forms.CheckboxInput(
                attrs={"class": "form-check-input", "title": "Show captions for audio content"}
            ),
            "screen_reader_mode": forms.CheckboxInput(
                attrs={"class": "form-check-input", "title": "Optimize for screen reader compatibility"}
            ),
        }
