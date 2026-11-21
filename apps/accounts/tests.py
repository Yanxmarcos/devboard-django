from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountTests(TestCase):
    def test_profile_is_created_with_user(self):
        user = User.objects.create_user(username="alex", password="safe-test-password")
        self.assertEqual(user.profile.user, user)

    def test_signup_creates_authenticated_user(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newuser",
                "first_name": "New",
                "last_name": "User",
                "email": "new@example.com",
                "password1": "Strong-test-password-2026",
                "password2": "Strong-test-password-2026",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user("existing", email="same@example.com", password="test-password")
        response = self.client.post(
            reverse("signup"),
            {
                "username": "another",
                "first_name": "Another",
                "last_name": "User",
                "email": "same@example.com",
                "password1": "Strong-test-password-2026",
                "password2": "Strong-test-password-2026",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe una cuenta")

    def test_user_can_update_profile(self):
        user = User.objects.create_user("profile-user", password="test-password")
        self.client.force_login(user)
        response = self.client.post(
            reverse("profile"),
            {
                "first_name": "Alex",
                "last_name": "Rivera",
                "email": "alex@example.com",
                "job_title": "Backend Developer",
                "location": "Trujillo",
                "bio": "Django developer",
            },
        )
        self.assertRedirects(response, reverse("profile"))
        user.refresh_from_db()
        self.assertEqual(user.profile.job_title, "Backend Developer")
