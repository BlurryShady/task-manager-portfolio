from django.contrib import admin
from .models import Workspace, Project, Column, Task, Tag, ActivityLog

@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name","owner","created_at")
    search_fields = ("name", "owner__username")

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title","workspace","created_at")
    list_filter = ("workspace",)
    search_fields = ("title", "workspace__name")

@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ("name","project","order")
    list_editable = ("order",)
    search_fields = ("name", "project__title")

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name","color")
    search_fields = ("name",)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title","project","column","priority","due_date","created_at")
    list_filter = ("project","priority","due_date","tags")
    search_fields = ("title","description")
    autocomplete_fields = ("project","column","creator","assignees","tags")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "ip_address", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("action", "user__username", "metadata")
    readonly_fields = (
        "created_at",
        "user",
        "action",
        "metadata",
        "request_path",
        "ip_address",
        "user_agent",
    )

