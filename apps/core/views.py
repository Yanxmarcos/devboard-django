from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from apps.projects.models import Project, ProjectMembership
from apps.tasks.models import Activity, Task


class HomeView(TemplateView):
    template_name = "core/home.html"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        projects = Project.objects.for_user(user)
        tasks = Task.objects.filter(project__in=projects)

        context.update(
            {
                "project_count": projects.count(),
                "owned_project_count": projects.filter(owner=user).count(),
                "open_task_count": tasks.exclude(status=Task.Status.DONE).count(),
                "overdue_task_count": tasks.exclude(status=Task.Status.DONE)
                .filter(due_date__lt=timezone.localdate())
                .count(),
                "my_tasks": tasks.filter(assignee=user)
                .exclude(status=Task.Status.DONE)
                .select_related("project")[:6],
                "recent_projects": projects.annotate(
                    total_tasks=Count("tasks"),
                    completed_tasks=Count(
                        "tasks", filter=Q(tasks__status=Task.Status.DONE)
                    ),
                )[:5],
                "recent_activity": Activity.objects.filter(project__in=projects)
                .select_related("user", "project", "task")[:8],
                "status_labels": [label for _, label in Task.Status.choices],
                "status_values": [
                    tasks.filter(status=value).count()
                    for value, _ in Task.Status.choices
                ],
                "membership_count": ProjectMembership.objects.filter(user=user).count(),
            }
        )
        return context
