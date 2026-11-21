from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.tasks.models import Activity, Task

from .forms import MemberForm, MemberRoleForm, ProjectForm
from .models import Project, ProjectMembership


class ProjectAccessMixin(LoginRequiredMixin):
    project = None
    require_owner = False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.project = get_object_or_404(
            Project.objects.for_user(request.user), slug=kwargs["slug"]
        )
        if self.require_owner and request.user != self.project.owner:
            return HttpResponseForbidden("Solo el propietario puede realizar esta acción.")
        return super().dispatch(request, *args, **kwargs)


class ProjectOwnerMixin(ProjectAccessMixin):
    require_owner = True


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    paginate_by = 9

    def get_queryset(self):
        queryset = Project.objects.for_user(self.request.user).annotate(
            task_count=Count("tasks"),
            done_count=Count("tasks", filter=Q(tasks__status=Task.Status.DONE)),
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        return queryset


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        ProjectMembership.objects.create(
            project=self.object,
            user=self.request.user,
            role=ProjectMembership.Role.OWNER,
        )
        Activity.objects.create(
            project=self.object,
            user=self.request.user,
            action=Activity.Action.PROJECT_CREATED,
            description="creó el proyecto",
        )
        messages.success(self.request, "Proyecto creado correctamente.")
        return response


class ProjectDetailView(ProjectAccessMixin, DetailView):
    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_object(self, queryset=None):
        return self.project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = self.project.tasks.select_related("assignee", "created_by").prefetch_related("comments")
        priority = self.request.GET.get("priority")
        assignee = self.request.GET.get("assignee")
        if priority in Task.Priority.values:
            tasks = tasks.filter(priority=priority)
        if assignee == "me":
            tasks = tasks.filter(assignee=self.request.user)
        context.update(
            {
                "tasks_by_status": [
                    (value, label, tasks.filter(status=value))
                    for value, label in Task.Status.choices
                ],
                "memberships": self.project.memberships.select_related("user"),
                "member_form": MemberForm(),
                "role": self.project.role_for(self.request.user),
                "can_edit": self.project.can_edit(self.request.user),
                "priorities": Task.Priority.choices,
                "statuses": Task.Status.choices,
            }
        )
        return context


class ProjectUpdateView(ProjectOwnerMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"

    def get_object(self, queryset=None):
        return self.project

    def form_valid(self, form):
        messages.success(self.request, "Proyecto actualizado.")
        return super().form_valid(form)


class ProjectDeleteView(ProjectOwnerMixin, DeleteView):
    model = Project
    template_name = "projects/project_confirm_delete.html"
    success_url = reverse_lazy("project_list")

    def get_object(self, queryset=None):
        return self.project

    def form_valid(self, form):
        messages.success(self.request, "Proyecto eliminado.")
        return super().form_valid(form)


class MemberAddView(ProjectOwnerMixin, View):
    def post(self, request, *args, **kwargs):
        form = MemberForm(request.POST)
        if form.is_valid():
            if form.user == self.project.owner:
                messages.info(request, "El propietario ya forma parte del proyecto.")
            else:
                membership, created = ProjectMembership.objects.get_or_create(
                    project=self.project,
                    user=form.user,
                    defaults={"role": form.cleaned_data["role"]},
                )
                if created:
                    Activity.objects.create(
                        project=self.project,
                        user=request.user,
                        action=Activity.Action.MEMBER_ADDED,
                        description=f"añadió a {form.user.username} al proyecto",
                    )
                    messages.success(request, "Miembro añadido correctamente.")
                else:
                    messages.info(request, "Esa persona ya pertenece al proyecto.")
        else:
            messages.error(request, next(iter(form.errors.values()))[0])
        return redirect(self.project)


class MemberRoleUpdateView(ProjectOwnerMixin, View):
    def post(self, request, *args, **kwargs):
        membership = get_object_or_404(
            self.project.memberships.exclude(user=self.project.owner), pk=kwargs["pk"]
        )
        form = MemberRoleForm(request.POST, instance=membership)
        if form.is_valid():
            form.save()
            messages.success(request, "Rol actualizado.")
        return redirect(self.project)


class MemberRemoveView(ProjectOwnerMixin, View):
    def post(self, request, *args, **kwargs):
        membership = get_object_or_404(
            self.project.memberships.exclude(user=self.project.owner), pk=kwargs["pk"]
        )
        username = membership.user.username
        membership.delete()
        Activity.objects.create(
            project=self.project,
            user=request.user,
            action=Activity.Action.MEMBER_REMOVED,
            description=f"retiró a {username} del proyecto",
        )
        messages.success(request, "Miembro retirado del proyecto.")
        return redirect(self.project)
