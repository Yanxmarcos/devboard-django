from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.projects.models import Project, ProjectMembership

from .models import Comment, Task


class TaskTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="test-password")
        self.collaborator = User.objects.create_user("collab", password="test-password")
        self.viewer = User.objects.create_user("viewer", password="test-password")
        self.outsider = User.objects.create_user("other", password="test-password")
        self.project = Project.objects.create(name="DevBoard", owner=self.owner)
        ProjectMembership.objects.create(project=self.project, user=self.owner, role="owner")
        ProjectMembership.objects.create(project=self.project, user=self.collaborator, role="collaborator")
        ProjectMembership.objects.create(project=self.project, user=self.viewer, role="viewer")
        self.task = Task.objects.create(
            project=self.project,
            title="Write tests",
            created_by=self.owner,
            assignee=self.collaborator,
        )

    def test_assignee_must_be_project_member(self):
        self.task.assignee = self.outsider
        with self.assertRaises(ValidationError):
            self.task.full_clean()

    def test_collaborator_can_change_task_status(self):
        self.client.force_login(self.collaborator)
        response = self.client.post(
            reverse("task_status", kwargs={"pk": self.task.pk}),
            {"status": Task.Status.DONE},
        )
        self.assertRedirects(response, self.task.get_absolute_url())
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.DONE)

    def test_viewer_cannot_change_task_status(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("task_status", kwargs={"pk": self.task.pk}),
            {"status": Task.Status.DONE},
        )
        self.assertEqual(response.status_code, 403)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.TODO)

    def test_member_can_comment(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("comment_create", kwargs={"pk": self.task.pk}),
            {"body": "Looks good."},
        )
        self.assertRedirects(response, self.task.get_absolute_url())
        self.assertTrue(Comment.objects.filter(task=self.task, author=self.viewer).exists())

    def test_collaborator_can_create_task(self):
        self.client.force_login(self.collaborator)
        response = self.client.post(
            reverse("task_create", kwargs={"slug": self.project.slug}),
            {
                "title": "Implement feature",
                "description": "Portfolio feature",
                "status": Task.Status.TODO,
                "priority": Task.Priority.HIGH,
                "assignee": self.collaborator.pk,
                "due_date": "2030-01-20",
            },
        )
        task = Task.objects.get(title="Implement feature")
        self.assertRedirects(response, task.get_absolute_url())

    def test_viewer_cannot_create_task(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("task_create", kwargs={"slug": self.project.slug}),
            {"title": "Forbidden"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Task.objects.filter(title="Forbidden").exists())

    def test_outsider_cannot_view_task(self):
        self.client.force_login(self.outsider)
        response = self.client.get(self.task.get_absolute_url())
        self.assertEqual(response.status_code, 404)
