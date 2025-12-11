import logging
from .email_utils import send_brevo_email
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotAllowed,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.timezone import now

from .forms import (
    WorkspaceForm,
    ProjectForm,
    ColumnForm,
    TaskForm,
    CommentForm,
    InviteMemberForm,
    SignupForm,
    CustomAuthenticationForm,
)
from .models import Workspace, Project, Column, Task, WorkspaceMember
from .permissions import (
    user_in_workspace_or_403,
    user_can_see_project_or_403,
    user_is_workspace_owner,
)
from .telemetry import log_activity
import logging
from django.conf import settings
from django.core.mail import send_mail

User = get_user_model()
logger = logging.getLogger(__name__)
SITE_NAME = getattr(settings, "SITE_NAME", "Task Manager")


def render_form(request, page_template, ctx):
    is_partial = (
        request.GET.get("partial") == "1" or
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )
    return render(
        request,
        "boards/_form_inner.html" if is_partial else page_template,
        ctx
    )


logger = logging.getLogger(__name__)
SITE_NAME = getattr(settings, "SITE_NAME", "Task Manager")


def send_activation_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_url = request.build_absolute_uri(
        reverse("activate_account", args=[uid, token])
    )
    context = {
        "user": user,
        "activation_url": activation_url,
        "site_name": SITE_NAME,
    }
    subject = f"Activate your {SITE_NAME} account"
    message = render_to_string("emails/activation_email.txt", context)

    # Use Brevo HTTP helper (no SMTP)
    send_brevo_email(subject, message, user.email)

    log_activity(request, "activation_email_sent", user_id=user.pk)


def send_welcome_email(user):
    context = {"user": user, "site_name": SITE_NAME}
    subject = f"Welcome to {SITE_NAME}"
    message = render_to_string("emails/welcome_email.txt", context)

    # Use Brevo HTTP helper
    send_brevo_email(subject, message, user.email)

    log_activity(None, "welcome_email_sent", user_id=user.pk)

def signup(request):
    if request.user.is_authenticated:
        return redirect("workspace_list")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            email_ok = send_activation_email(request, user)

            log_activity(
                request,
                "signup_submitted",
                user_id=user.pk,
                email=user.email,
            )

            if email_ok:
                #  Email sent – standard flow
                return render(
                    request,
                    "registration/activation_sent.html",
                    {"email": user.email},
                )
            else:
                #  Email failed in production – tell the user and yourself
                messages.error(
                    request,
                    "We couldn't send the activation email right now. "
                    "Your account was created but is not active yet. "
                    "Please try again later."
                )
                return redirect("login")
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save()
            send_welcome_email(user)
        log_activity(request, "signup_activated", user_id=user.pk)
        login(request, user)
        messages.success(request, "Account verified! Welcome back.")
        return redirect("workspace_list")

    return render(
        request,
        "registration/activation_invalid.html",
        status=400,
    )


class WorkspaceLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = "registration/login.html"

# ---------- Workspaces ----------


@login_required
def workspace_list(request):
    qs_owned = Workspace.objects.filter(owner=request.user).order_by("name")
    qs_member = (
        Workspace.objects
        .filter(memberships__user=request.user)
        .exclude(owner=request.user)
        .distinct()
        .order_by("name")
    )
    context = {"owned": qs_owned, "member": qs_member}
    return render(request, "boards/workspace_list.html", context)


@login_required
def workspace_create(request):
    if request.method == "POST":
        form = WorkspaceForm(request.POST)
        if form.is_valid():
            ws = form.save(commit=False)
            ws.owner = request.user
            ws.save()
            log_activity(request, "workspace_created", workspace_id=ws.pk)
            messages.success(request, "Workspace created.")
            return redirect("workspace_detail", pk=ws.pk)
    else:
        form = WorkspaceForm()
    return render(
        request,
        "boards/workspace_form.html",
        {"form": form, "title": "New Workspace"},
    )


@login_required
def workspace_detail(request, pk):
    ws = user_in_workspace_or_403(request, pk)
    if not isinstance(ws, Workspace):
        return ws  # 403

    projects = ws.projects.order_by("-created_at")
    members = ws.memberships.select_related("user").order_by(
        "role", "user__username"
    )
    invite_form = InviteMemberForm()
    return render(
        request,
        "boards/workspace_detail.html",
        {
            "ws": ws,
            "projects": projects,
            "members": members,
            "invite_form": invite_form,
        },
    )


@login_required
def workspace_delete(request, pk):
    ws = get_object_or_404(Workspace, pk=pk)
    if not user_is_workspace_owner(request, ws):
        return HttpResponseForbidden("Only owner can delete workspace.")
    if request.method == "POST":
        ws.delete()
        messages.info(request, "Workspace deleted.")
        return redirect("workspace_list")
    return render(
        request,
        "boards/confirm_delete.html",
        {"obj": ws, "back_url": reverse("workspace_detail", args=[pk])},
    )

@login_required
def workspace_invite_member(request, pk):
    ws = user_in_workspace_or_403(request, pk)
    if not isinstance(ws, Workspace):
        return ws
    if ws.owner_id != request.user.id:
        return HttpResponseForbidden("Only owner can invite.")

    if request.method == "POST":
        form = InviteMemberForm(request.POST)
        if form.is_valid():
            user = form.user

            if user.id == request.user.id:
                messages.warning(request, "You are already in this workspace.")
                return redirect("workspace_detail", pk=ws.pk)

            if user.id == ws.owner_id:
                messages.info(
                    request,
                    f"{user.username} is already the owner.",
                )
                return redirect("workspace_detail", pk=ws.pk)

            if WorkspaceMember.objects.filter(
                workspace=ws,
                user=user,
            ).exists():
                messages.info(
                    request,
                    f"{user.username} is already a member.",
                )
                return redirect("workspace_detail", pk=ws.pk)

            WorkspaceMember.objects.create(
                workspace=ws,
                user=user,
                role="member",
            )
            messages.success(request, f"Invited {user.username} to {ws.name}.")
            return redirect("workspace_detail", pk=ws.pk)
    else:
        form = InviteMemberForm()

    return render(
        request,
        "boards/workspace_invite.html",
        {"ws": ws, "form": form},
    )

@login_required
def workspace_remove_member(request, pk, user_id):
    ws = user_in_workspace_or_403(request, pk)
    if not isinstance(ws, Workspace):
        return ws
    if ws.owner_id != request.user.id:
        return HttpResponseForbidden("Only owner can remove members.")
    if request.method == "POST":
        WorkspaceMember.objects.filter(workspace=ws, user_id=user_id).delete()
        messages.info(request, "Member removed.")
        return redirect("workspace_detail", pk=ws.pk)
    user = get_object_or_404(User, pk=user_id)
    return render(request, "boards/confirm_delete.html",
                  {"obj": f"{user.username} from {ws.name}",
                   "back_url": reverse("workspace_detail", args=[ws.pk])})

# ---------- Projects (Boards) ----------

@login_required
def project_create(request, ws_pk):
    ws = user_in_workspace_or_403(request, ws_pk)
    if not isinstance(ws, Workspace):
        return ws
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.workspace = ws
            project.save()
            log_activity(
                request,
                "project_created",
                workspace_id=ws.pk,
                project_id=project.pk,
            )
            # Seed default columns
            defaults = [("Backlog", "#111827"), ("Todo", "#1f2937"),
                        ("In Progress", "#374151"), ("Done", "#065f46")]
            for i, (name, color) in enumerate(defaults):
                Column.objects.create(project=project, name=name, order=i, color=color)
            messages.success(request, "Board created with default columns.")
            return redirect("project_detail", pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, "boards/project_form.html", {"form": form, "ws": ws})

@login_required
def project_detail(request, pk):
    project = user_can_see_project_or_403(request, pk)
    if not isinstance(project, Project):
        return project

    # Filters
    assignee = request.GET.get("assignee")  # "me" or user id
    tag_id = request.GET.get("tag")
    priority = request.GET.get("priority")
    overdue = request.GET.get("overdue")  # "1" => overdue only

    task_filters = {"archived": False, "project": project}
    if assignee == "me":
        task_filters["assignees__id"] = request.user.id
    elif assignee and assignee.isdigit():
        task_filters["assignees__id"] = int(assignee)
    if tag_id and tag_id.isdigit():
        task_filters["tags__id"] = int(tag_id)
    if priority in {"low", "medium", "high"}:
        task_filters["priority"] = priority

    today = now().date()

    columns = list(project.columns.all().order_by("order"))
    for col in columns:
        qs = Task.objects.filter(column=col, **task_filters)
        if overdue == "1":
            qs = qs.filter(due_date__lt=today)
        col.filtered_tasks = qs.select_related("project", "column").prefetch_related("tags", "assignees")

    from .models import Tag
    members = project.workspace.memberships.select_related("user").values_list("user_id", "user__username")
    tags = Tag.objects.all()

    return render(request, "boards/project_detail.html", {
        "project": project,
        "columns": columns,
        "filters": {"assignee": assignee, "tag": tag_id, "priority": priority, "overdue": overdue},
        "members": members,
        "tags": tags,
        "today": today,
    })

@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk)
    ws = project.workspace
    if not user_is_workspace_owner(request, ws):
        return HttpResponseForbidden("Only workspace owner can delete projects.")
    if request.method == "POST":
        project.delete()
        messages.info(request, "Project deleted.")
        return redirect("workspace_detail", pk=ws.pk)
    return render(request, "boards/confirm_delete.html",
                  {"obj": project, "back_url": reverse("workspace_detail", args=[ws.pk])})

# ---------- Columns ----------

@login_required
def column_create(request, project_pk):
    project = user_can_see_project_or_403(request, project_pk)
    if not isinstance(project, Project):
        return project

    if request.method == "POST":
        form = ColumnForm(request.POST)
        if form.is_valid():
            col = form.save(commit=False)
            col.project = project
            col.save()
            # modal/AJAX submit → let JS reload
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return HttpResponse(status=204)
            messages.success(request, "Column created.")
            return redirect("project_detail", pk=project.pk)
    else:
        form = ColumnForm()

    
    return render_form(request, "boards/column_form.html", {
        "form": form, "project": project,
        "form_action": reverse("column_create", args=[project.pk]),
    })



@login_required
def column_rename(request, pk):
    col = get_object_or_404(Column, pk=pk)
    project = user_can_see_project_or_403(request, col.project_id)
    if not isinstance(project, Project):
        return project

    if request.method == "POST":
        form = ColumnForm(request.POST, instance=col)
        if form.is_valid():
            form.save()
            # If called from the modal (AJAX), signal success with 204.
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return HttpResponse(status=204)
            messages.success(request, "Column renamed.")
            return redirect("project_detail", pk=project.pk)
    else:
        # ← Ensure form is always defined on GET
        form = ColumnForm(instance=col)

    return render_form(
        request,
        "boards/column_form.html",
        {
            "form": form,
            "project": project,
            "form_action": reverse("column_rename", args=[col.pk]),
        },
    )



@login_required
def column_delete(request, pk):
    column = get_object_or_404(Column, pk=pk)
    project = column.project
    if not isinstance(user_can_see_project_or_403(request, project.pk), Project):
        return HttpResponseForbidden("Not allowed")
    if request.method == "POST":
        column.delete()
        messages.info(request, "Column deleted.")
        return redirect("project_detail", pk=project.pk)
    return render(request, "boards/confirm_delete.html",
                  {"obj": column, "back_url": reverse("project_detail", args=[project.pk])})

# ---------- Tasks ----------

@login_required
def task_create(request, project_pk):
    
    project = user_can_see_project_or_403(request, project_pk)
    if not isinstance(project, Project):
        return project  

    workspace = project.workspace  # used to filter assignees

    if request.method == "POST":
        form = TaskForm(request.POST, workspace=workspace)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.creator = request.user  

            # Default to first column if none chosen
            if not task.column_id:
                first_col = project.columns.order_by("order").first()
                task.column = first_col

            task.save()
            form.save_m2m()

            log_activity(
                request,
                "task_created",
                project_id=project.pk,
                task_id=task.pk,
            )

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return HttpResponse(status=204)

            messages.success(request, "Task created successfully!")
            return redirect("project_detail", project.pk)
    else:
        initial = {}
        col = request.GET.get("column")
        if col and col.isdigit():
            initial["column"] = int(col)
        form = TaskForm(initial=initial, workspace=workspace)

    return render_form(
        request,
        "boards/task_form.html",
        {
            "form": form,
            "project": project,
            "form_action": reverse("task_create", args=[project.pk]),
        },
    )



@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project_perm = user_can_see_project_or_403(request, task.project.pk)
    if not isinstance(project_perm, Project):
        return HttpResponseForbidden("Not allowed")

    workspace = task.project.workspace

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task, workspace=workspace)
        if form.is_valid():
            form.save()
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return HttpResponse(status=204)
            messages.success(request, "Task updated.")
            return redirect("project_detail", pk=task.project.pk)
    else:
        form = TaskForm(instance=task, workspace=workspace)

    return render_form(
        request,
        "boards/task_form.html",
        {
            "form": form,
            "project": task.project,
            "form_action": reverse("task_edit", args=[task.pk]),
        },
    )

@login_required
def task_archive(request, pk):
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    if not isinstance(user_can_see_project_or_403(request, project.pk), Project):
        return HttpResponseForbidden("Not allowed")

    is_owner = project.workspace.owner_id == request.user.id
    is_creator = task.creator_id == request.user.id
    is_assignee = task.assignees.filter(pk=request.user.id).exists()
    if not (is_owner or is_creator or is_assignee):
        return HttpResponseForbidden("Only owner, creator, or assignee can archive.")

    if request.method == "POST":
        task.archived = True
        task.save(update_fields=["archived"])
        messages.info(request, "Task archived.")
        return redirect("project_detail", pk=project.pk)
    return render(request, "boards/confirm_archive.html", {"task": task})

@login_required
def task_move(request, pk, column_pk):
    task = get_object_or_404(Task, pk=pk)
    project = task.project
    perm = user_can_see_project_or_403(request, project.pk)
    if not isinstance(perm, Project):
        return perm

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    column = get_object_or_404(Column, pk=column_pk, project=project)
    task.column = column
    task.save(update_fields=["column"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "task": pk, "column": column_pk})

    messages.success(request, "Task moved.")
    return redirect("project_detail", pk=project.pk)

# ---------- Comments ----------

@login_required
def comment_create(request, task_pk):
    task = get_object_or_404(Task, pk=task_pk)
    if not isinstance(user_can_see_project_or_403(request, task.project.pk), Project):
        return HttpResponseForbidden("Not allowed")
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.task = task
            c.author = request.user
            c.save()
            messages.success(request, "Comment added.")
            return redirect("project_detail", pk=task.project.pk)
    else:
        form = CommentForm()
    return render(request, "boards/comment_form.html", {"form": form, "task": task})


@login_required
def project_clear_tasks(request, pk):
    # Authorize via the workspace owner (adjust later if you add members)
    project = get_object_or_404(
        Project.objects.select_related('workspace'),
        pk=pk,
        workspace__owner=request.user
    )

    if request.method == "POST":
        # If Task is FK to Column, and Column FK to Project, clear via column__project
        Task.objects.filter(column__project=project).delete()

        # AJAX → 204, otherwise redirect back to board
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return HttpResponse(status=204)
        return redirect("project_detail", pk=project.pk)

    # GET → show confirmation (partial if requested)
    template = "boards/partials/confirm_clear.html" if request.GET.get("partial") else "boards/confirm_clear.html"
    return render(request, template, {"project": project})
