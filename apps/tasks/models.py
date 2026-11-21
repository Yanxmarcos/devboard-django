from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from apps.projects.models import Project


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = "todo", "Pendiente"
        IN_PROGRESS = "in_progress", "En progreso"
        REVIEW = "review", "En revisión"
        DONE = "done", "Completada"

    class Priority(models.TextChoices):
        LOW = "low", "Baja"
        MEDIUM = "medium", "Media"
        HIGH = "high", "Alta"
        URGENT = "urgent", "Urgente"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="created_tasks")
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("due_date", "-created_at")

    def clean(self):
        if self.assignee_id and self.project_id:
            is_member = self.project.memberships.filter(user=self.assignee).exists()
            if not is_member and self.project.owner_id != self.assignee_id:
                raise ValidationError({"assignee": "La persona asignada debe pertenecer al proyecto."})

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("task_detail", kwargs={"pk": self.pk})


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_comments")
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Comentario de {self.author.username}"


class Activity(models.Model):
    class Action(models.TextChoices):
        PROJECT_CREATED = "project_created", "Proyecto creado"
        TASK_CREATED = "task_created", "Tarea creada"
        TASK_UPDATED = "task_updated", "Tarea actualizada"
        TASK_STATUS = "task_status", "Estado modificado"
        COMMENT_ADDED = "comment_added", "Comentario añadido"
        MEMBER_ADDED = "member_added", "Miembro añadido"
        MEMBER_REMOVED = "member_removed", "Miembro retirado"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="activities")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="activities", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="activities", null=True)
    action = models.CharField(max_length=30, choices=Action.choices)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name_plural = "activities"

    def __str__(self):
        return self.description
