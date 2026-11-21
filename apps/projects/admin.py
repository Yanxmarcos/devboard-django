from django.contrib import admin

from .models import Project, ProjectMembership


class MembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "is_archived", "updated_at")
    list_filter = ("is_archived", "created_at")
    search_fields = ("name", "description", "owner__username")
    readonly_fields = ("slug", "created_at", "updated_at")
    inlines = (MembershipInline,)


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "role", "joined_at")
    list_filter = ("role",)
    search_fields = ("user__username", "project__name")
