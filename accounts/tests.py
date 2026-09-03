from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AccountSettingsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="EMP300", employee_id="EMP300", email="employee@example.com",
            first_name="Employee", password="OldPass123!",
        )
        self.other = User.objects.create_user(
            username="EMP301", employee_id="EMP301", email="other@example.com", password="x"
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

    def test_profile_updates_name_and_email(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("update_profile"),
            {"first_name": "Updated", "last_name": "Person", "email": "updated@example.com"},
        )
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertEqual(self.user.department, "")

    def test_profile_rejects_duplicate_email(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("update_profile"),
            {"first_name": "Employee", "last_name": "", "email": self.other.email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email already exists.")

    def test_password_change_keeps_user_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("change_password"),
            {"old_password": "OldPass123!", "new_password1": "NewPass123!", "new_password2": "NewPass123!"},
        )
        self.assertRedirects(response, reverse("profile"))
        self.assertIn("_auth_user_id", self.client.session)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass123!"))
