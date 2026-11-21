from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

from apps.projects.models import Project

from .forms import CommentForm, TaskForm
from .models import Activity, Task


class TaskAccessMixin(LoginRequiredMixin):
    task = None
    require_edit = False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.task = get_object_or_404(
            Task.objects.select_related("project", "assignee", "created_by").filter(
                project__in=Project.objects.for_user(request.user)
            ).prefetch_related("comments__author"),
            pk=kwargs["pk"],
        )
        if self.require_edit and not self.task.project.can_edit(request.user):
            return HttpResponseForbidden("No tienes permiso para modificar tareas.")
        return super().dispatch(request, *args, **kwargs)


class TaskEditMixin(TaskAccessMixin):
    require_edit = True


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project.objects.for_user(request.user), slug=kwargs["slug"])
        if not self.project.can_edit(request.user):
            return HttpResponseForbidden("No tienes permiso para crear tareas.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.project
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.project
        return context

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        Activity.objects.create(
            project=self.project,
            task=self.object,
            user=self.request.user,
            action=Activity.Action.TASK_CREATED,
            description=f"creó la tarea «{self.object.title}»",
        )
        messages.success(self.request, "Tarea creada.")
        return response


class TaskDetailView(TaskAccessMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def get_object(self, queryset=None):
        return self.task

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm()
        context["can_edit"] = self.task.project.can_edit(self.request.user)
        context["statuses"] = Task.Status.choices
        return context


class TaskUpdateView(TaskEditMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def get_object(self, queryset=None):
        return self.task

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.task.project
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        Activity.objects.create(
            project=self.task.project,
            task=self.object,
            user=self.request.user,
            action=Activity.Action.TASK_UPDATED,
            description=f"actualizó la tarea «{self.object.title}»",
        )
        messages.success(self.request, "Tarea actualizada.")
        return response


class TaskDeleteView(TaskEditMixin, DeleteView):
    model = Task
    template_name = "tasks/task_confirm_delete.html"

    def get_object(self, queryset=None):
        return self.task

    def get_success_url(self):
        return self.task.project.get_absolute_url()

    def form_valid(self, form):
        messages.success(self.request, "Tarea eliminada.")
        return super().form_valid(form)


class TaskStatusView(TaskEditMixin, View):
    def post(self, request, *args, **kwargs):
        status = request.POST.get("status")
        if status not in Task.Status.values:
            messages.error(request, "El estado indicado no es válido.")
            return redirect(self.task)
        old_status = self.task.get_status_display()
        self.task.status = status
        self.task.save(update_fields=("status", "updated_at"))
        Activity.objects.create(
            project=self.task.project,
            task=self.task,
            user=request.user,
            action=Activity.Action.TASK_STATUS,
            description=f"movió «{self.task.title}» de {old_status} a {self.task.get_status_display()}",
        )
        messages.success(request, "Estado actualizado.")
        next_url = request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(next_url)
        return redirect(self.task)


class CommentCreateView(TaskAccessMixin, View):
    def post(self, request, *args, **kwargs):
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = self.task
            comment.author = request.user
            comment.save()
            Activity.objects.create(
                project=self.task.project,
                task=self.task,
                user=request.user,
                action=Activity.Action.COMMENT_ADDED,
                description=f"comentó en «{self.task.title}»",
            )
            messages.success(request, "Comentario publicado.")
        return redirect(self.task)
