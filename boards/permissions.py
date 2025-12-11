from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .models import Workspace, Project

def user_in_workspace_or_403(request, workspace_id):
    ws = get_object_or_404(Workspace, pk=workspace_id)
    if ws.owner_id == request.user.id or ws.memberships.filter(user=request.user).exists():
        return ws
    return HttpResponseForbidden("Not allowed")

def user_can_see_project_or_403(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    ws = project.workspace
    if ws.owner_id == request.user.id or ws.memberships.filter(user=request.user).exists():
        return project
    return HttpResponseForbidden("Not allowed")

def user_is_workspace_owner(request, workspace):
    return workspace.owner_id == request.user.id
