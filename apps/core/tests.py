from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class CoreViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("dashboard-user", password="test-password")

    def test_landing_page_is_public(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Convierte las ideas")

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_authenticated_dashboard_renders(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tareas abiertas")
