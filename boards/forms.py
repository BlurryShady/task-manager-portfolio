from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Workspace, Project, Column, Task, Comment, WorkspaceMember




User = get_user_model()


class WorkspaceForm(forms.ModelForm):
    class Meta:
        model = Workspace
        fields = ["name"]


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title"]


class ColumnForm(forms.ModelForm):
    class Meta:
        model = Column
        fields = ["name", "color", "order"]
        widgets = {
            "color": forms.TextInput(attrs={"type": "color"})
        }


class TaskForm(forms.ModelForm):
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d'],
    )

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "priority",
            "due_date",
            "assignees",
            "tags",
            "column",
        ]
        labels = {
            "description": "Notes",
        }
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Notes…"}
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Accept a `workspace` kwarg so we can limit assignees
        to users who are actually in that workspace.
        """
        workspace = kwargs.pop("workspace", None)
        super().__init__(*args, **kwargs)

        if workspace is not None:
            # workspace.memberships is the related name to WorkspaceMember
            member_ids = list(
                workspace.memberships.values_list("user_id", flat=True)
            )
            # include the owner too
            member_ids.append(workspace.owner_id)

            self.fields["assignees"].queryset = User.objects.filter(
                id__in=member_ids
            ).order_by("username")
        else:
            # if no workspace provided, don't show any users
            self.fields["assignees"].queryset = User.objects.none()


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]


class InviteMemberForm(forms.Form):
    identifier = forms.CharField(
        label="Username or Email",
        help_text="Invite an existing user by username or email."
    )

    def clean_identifier(self):
        ident = self.cleaned_data["identifier"].strip()
        try:
            user = User.objects.get(username=ident)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email__iexact=ident)
            except User.DoesNotExist:
                raise forms.ValidationError(
                    "No user with that username or email."
                )
        self.user = user
        return ident


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email",)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"].lower()
        user.email = email
        user.is_active = False
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                "Please verify your email before signing in.",
                code="inactive",
            )
        return super().confirm_login_allowed(user)
