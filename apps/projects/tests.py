from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Project, ProjectMembership


class ProjectTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="test-password")
        self.viewer = User.objects.create_user("viewer", password="test-password")
        self.outsider = User.objects.create_user("outsider", password="test-password")
        self.project = Project.objects.create(name="Portfolio", owner=self.owner)
        ProjectMembership.objects.create(project=self.project, user=self.owner, role="owner")
        ProjectMembership.objects.create(project=self.project, user=self.viewer, role="viewer")

    def test_for_user_returns_only_accessible_projects(self):
        self.assertIn(self.project, Project.objects.for_user(self.viewer))
        self.assertNotIn(self.project, Project.objects.for_user(self.outsider))

    def test_project_creation_adds_owner_membership(self):
        self.client.force_login(self.outsider)
        response = self.client.post(
            reverse("project_create"),
            {"name": "Nuevo", "description": "Proyecto", "color": "#123456"},
        )
        project = Project.objects.get(name="Nuevo")
        self.assertRedirects(response, project.get_absolute_url())
        self.assertTrue(project.memberships.filter(user=self.outsider, role="owner").exists())

    def test_viewer_cannot_update_project(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("project_update", kwargs={"slug": self.project.slug}),
            {"name": "Changed", "description": "", "color": "#123456"},
        )
        self.assertEqual(response.status_code, 403)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Portfolio")

    def test_outsider_cannot_see_project(self):
        self.client.force_login(self.outsider)
        response = self.client.get(self.project.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_owner_can_add_member(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("member_add", kwargs={"slug": self.project.slug}),
            {"identifier": self.outsider.email or self.outsider.username, "role": "collaborator"},
        )
        self.assertRedirects(response, self.project.get_absolute_url())
        self.assertTrue(self.project.memberships.filter(user=self.outsider, role="collaborator").exists())

    def test_viewer_cannot_add_member(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("member_add", kwargs={"slug": self.project.slug}),
            {"identifier": self.outsider.username, "role": "collaborator"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.project.memberships.filter(user=self.outsider).exists())
