from django.contrib import admin

from .models import Activity, Comment, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "status", "priority", "assignee", "due_date")
    list_filter = ("status", "priority", "project")
    search_fields = ("title", "description", "project__name")
    autocomplete_fields = ("assignee", "created_by")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")
    search_fields = ("body", "task__title", "author__username")


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("project", "user", "action", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("description", "project__name", "user__username")
