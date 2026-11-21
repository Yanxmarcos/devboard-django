from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.projects.models import Project, ProjectMembership
from apps.tasks.models import Activity, Comment, Task


class Command(BaseCommand):
    help = "Creates an idempotent demo workspace for local evaluation."

    def handle(self, *args, **options):
        owner, owner_created = User.objects.get_or_create(
            username="demo",
            defaults={"email": "demo@devboard.local", "first_name": "Alex", "last_name": "Rivera"},
        )
        if owner_created:
            owner.set_password("DevBoard2026!")
            owner.save()

        collaborator, collaborator_created = User.objects.get_or_create(
            username="marina",
            defaults={"email": "marina@devboard.local", "first_name": "Marina", "last_name": "Torres"},
        )
        if collaborator_created:
            collaborator.set_password("DevBoard2026!")
            collaborator.save()

        project, project_created = Project.objects.get_or_create(
            name="Lanzamiento de plataforma",
            owner=owner,
            defaults={
                "description": "Planificación y seguimiento de una nueva plataforma digital.",
                "color": "#5B5BD6",
            },
        )
        ProjectMembership.objects.get_or_create(project=project, user=owner, defaults={"role": ProjectMembership.Role.OWNER})
        ProjectMembership.objects.get_or_create(project=project, user=collaborator, defaults={"role": ProjectMembership.Role.COLLABORATOR})

        task_specs = [
            ("Definir alcance del MVP", Task.Status.DONE, Task.Priority.HIGH, owner, -2),
            ("Diseñar la página principal", Task.Status.IN_PROGRESS, Task.Priority.HIGH, collaborator, 2),
            ("Preparar contenido de lanzamiento", Task.Status.TODO, Task.Priority.MEDIUM, owner, 5),
            ("Revisar flujo de registro", Task.Status.REVIEW, Task.Priority.URGENT, collaborator, 1),
            ("Configurar métricas iniciales", Task.Status.TODO, Task.Priority.LOW, None, 8),
        ]
        for title, status, priority, assignee, days in task_specs:
            task, created = Task.objects.get_or_create(
                project=project,
                title=title,
                defaults={
                    "description": f"Criterios y entregables para: {title.lower()}.",
                    "status": status,
                    "priority": priority,
                    "assignee": assignee,
                    "created_by": owner,
                    "due_date": timezone.localdate() + timedelta(days=days),
                },
            )
            if created:
                Activity.objects.create(
                    project=project,
                    task=task,
                    user=owner,
                    action=Activity.Action.TASK_CREATED,
                    description=f"creó la tarea «{task.title}»",
                )

        review_task = project.tasks.get(title="Revisar flujo de registro")
        Comment.objects.get_or_create(
            task=review_task,
            author=collaborator,
            body="El flujo principal está listo. Falta validar los mensajes de error.",
        )
        if project_created:
            Activity.objects.create(
                project=project,
                user=owner,
                action=Activity.Action.PROJECT_CREATED,
                description="creó el proyecto",
            )
        self.stdout.write(self.style.SUCCESS("Demo lista: usuario demo / DevBoard2026!"))
