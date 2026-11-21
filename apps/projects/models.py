import uuid

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse


class ProjectQuerySet(models.QuerySet):
    def for_user(self, user):
        if not user.is_authenticated:
            return self.none()
        return self.filter(Q(owner=user) | Q(memberships__user=user)).distinct()


class Project(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=160, unique=True, editable=False)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_projects"
    )
    color = models.CharField(
        max_length=7,
        default="#5B5BD6",
        validators=[
            RegexValidator(
                regex=r"^#[0-9A-Fa-f]{6}$",
                message="Usa un color hexadecimal válido, por ejemplo #5B5BD6.",
            )
        ],
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProjectQuerySet.as_manager()

    class Meta:
        ordering = ("-updated_at",)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            base = slugify(self.name)[:120] or "project"
            self.slug = f"{base}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_detail", kwargs={"slug": self.slug})

    def role_for(self, user):
        if user == self.owner:
            return ProjectMembership.Role.OWNER
        membership = self.memberships.filter(user=user).first()
        return membership.role if membership else None

    def can_edit(self, user):
        return self.role_for(user) in {
            ProjectMembership.Role.OWNER,
            ProjectMembership.Role.COLLABORATOR,
        }


class ProjectMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Propietario"
        COLLABORATOR = "collaborator", "Colaborador"
        VIEWER = "viewer", "Observador"

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="project_memberships"
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.COLLABORATOR
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("project", "user"), name="unique_project_member"
            )
        ]
        ordering = ("role", "user__username")

    def __str__(self):
        return f"{self.user.username} · {self.project.name}"
