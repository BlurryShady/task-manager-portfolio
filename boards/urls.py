from django.urls import path

from . import views


urlpatterns = [
    path("accounts/signup/", views.signup, name="signup"),
    path(
        "accounts/activate/<uidb64>/<token>/",
        views.activate_account,
        name="activate_account",
    ),
    # Workspaces
    path("", views.workspace_list, name="workspace_list"),
    path("workspaces/new/", views.workspace_create, name="workspace_create"),
    path(
        "workspaces/<int:pk>/",
        views.workspace_detail,
        name="workspace_detail",
    ),
    path(
        "workspaces/<int:pk>/delete/",
        views.workspace_delete,
        name="workspace_delete",
    ),
    # Projects (Boards)
    path(
        "workspaces/<int:ws_pk>/projects/new/",
        views.project_create,
        name="project_create",
    ),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path(
        "projects/<int:pk>/delete/",
        views.project_delete,
        name="project_delete",
    ),
    # Columns
    path(
        "projects/<int:project_pk>/columns/new/",
        views.column_create,
        name="column_create",
    ),
    path(
        "columns/<int:pk>/rename/",
        views.column_rename,
        name="column_rename",
    ),
    path(
        "columns/<int:pk>/delete/",
        views.column_delete,
        name="column_delete",
    ),
    # Tasks
    path(
        "projects/<int:project_pk>/tasks/new/",
        views.task_create,
        name="task_create",
    ),
    path("tasks/<int:pk>/edit/", views.task_edit, name="task_edit"),
    path("tasks/<int:pk>/archive/", views.task_archive, name="task_archive"),
    path(
        "tasks/<int:pk>/move/<int:column_pk>/",
        views.task_move,
        name="task_move",
    ),
    # Comments
    path(
        "tasks/<int:task_pk>/comments/new/",
        views.comment_create,
        name="comment_create",
    ),
    # Workspace members
    path(
        "workspaces/<int:pk>/members/invite/",
        views.workspace_invite_member,
        name="workspace_invite_member",
    ),
    path(
        "workspaces/<int:pk>/members/<int:user_id>/remove/",
        views.workspace_remove_member,
        name="workspace_remove_member",
    ),
    path(
        "projects/<int:pk>/clear/",
        views.project_clear_tasks,
        name="project_clear",
    ),
]
