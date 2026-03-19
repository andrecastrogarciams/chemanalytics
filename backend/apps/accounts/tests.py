from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import AdministrativeActionLog, UserProfile


class AuthenticationTests(APITestCase):
    def setUp(self):
        for group_name in ("admin", "reviewer", "consulta"):
            Group.objects.get_or_create(name=group_name)

        self.reviewer = User.objects.create_user(
            username="reviewer_user",
            password="Temp12345",
            is_active=True,
        )
        self.reviewer.groups.add(Group.objects.get(name="reviewer"))
        reviewer_profile = self.reviewer.profile
        reviewer_profile.role = "reviewer"
        reviewer_profile.must_change_password = True
        reviewer_profile.save()

        self.admin_user = User.objects.create_user(
            username="admin_user",
            password="Admin12345",
            is_active=True,
        )
        self.admin_user.groups.add(Group.objects.get(name="admin"))
        admin_profile = self.admin_user.profile
        admin_profile.role = "admin"
        admin_profile.must_change_password = False
        admin_profile.save()

        self.consulta = User.objects.create_user(
            username="consulta_user",
            password="Temp12345",
            is_active=True,
        )
        self.consulta.groups.add(Group.objects.get(name="consulta"))
        consulta_profile = self.consulta.profile
        consulta_profile.role = "consulta"
        consulta_profile.must_change_password = False
        consulta_profile.save()

        self.inactive = User.objects.create_user(
            username="inactive_user",
            password="Temp12345",
            is_active=False,
        )
        inactive_profile = self.inactive.profile
        inactive_profile.role = "reviewer"
        inactive_profile.save()

    def test_login_returns_tokens_and_profile(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": "reviewer_user", "password": "Temp12345"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"])
        self.assertEqual(response.data["data"]["user"]["group"], "reviewer")
        self.assertTrue(response.data["data"]["user"]["must_change_password"])

    def test_login_fails_with_invalid_credentials(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": "reviewer_user", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["code"], "INVALID_CREDENTIALS")

    def test_inactive_user_returns_403(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": "inactive_user", "password": "Temp12345"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "USER_INACTIVE")

    def test_change_password_clears_must_change_password(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "reviewer_user", "password": "Temp12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")

        response = self.client.post(
            reverse("auth-change-password"),
            {"current_password": "Temp12345", "new_password": "NewTemp12345"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reviewer.refresh_from_db()
        self.assertFalse(self.reviewer.profile.must_change_password)

    def test_permission_block_for_consulta_user(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "consulta_user", "password": "Temp12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")

        response = self.client.get(reverse("protected-reviewer"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_allows_reviewer_user(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "reviewer_user", "password": "Temp12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")

        response = self.client.get(reverse("protected-reviewer"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminUserManagementTests(APITestCase):
    def setUp(self):
        for group_name in ("admin", "reviewer", "consulta"):
            Group.objects.get_or_create(name=group_name)

        self.admin_user = User.objects.create_user(
            username="admin_manager",
            password="Admin12345",
            is_active=True,
        )
        self.admin_user.groups.add(Group.objects.get(name="admin"))
        profile = self.admin_user.profile
        profile.role = "admin"
        profile.must_change_password = False
        profile.save()

        self.reviewer = User.objects.create_user(
            username="reviewer_blocked",
            password="Temp12345",
            is_active=True,
        )
        self.reviewer.groups.add(Group.objects.get(name="reviewer"))
        reviewer_profile = self.reviewer.profile
        reviewer_profile.role = "reviewer"
        reviewer_profile.must_change_password = False
        reviewer_profile.save()

    def _login_as_admin(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "admin_manager", "password": "Admin12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")

    def _login_as_reviewer(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "reviewer_blocked", "password": "Temp12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")

    def test_admin_can_create_user(self):
        self._login_as_admin()

        response = self.client.post(
            reverse("admin-user-collection"),
            {
                "username": "new_consulta",
                "first_name": "Nova",
                "last_name": "Consulta",
                "role": "consulta",
                "temporary_password": "Temp12345",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = User.objects.get(username="new_consulta")
        self.assertTrue(created.is_active)
        self.assertEqual(created.profile.role, "consulta")
        self.assertTrue(created.profile.must_change_password)
        self.assertEqual(AdministrativeActionLog.objects.filter(action="create_user").count(), 1)

    def test_admin_can_update_role_and_deactivate_user(self):
        self._login_as_admin()

        target = User.objects.create_user(username="target_user", password="Temp12345", is_active=True)
        target.groups.add(Group.objects.get(name="consulta"))
        target_profile = target.profile
        target_profile.role = "consulta"
        target_profile.must_change_password = False
        target_profile.save()

        response = self.client.patch(
            reverse("admin-user-detail", args=[target.id]),
            {"role": "reviewer", "is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        target.refresh_from_db()
        self.assertFalse(target.is_active)
        self.assertEqual(target.profile.role, "reviewer")
        self.assertEqual(AdministrativeActionLog.objects.filter(action="update_role", target_user=target).count(), 1)
        self.assertEqual(AdministrativeActionLog.objects.filter(action="deactivate_user", target_user=target).count(), 1)

    def test_inactive_user_cannot_login_after_admin_deactivation(self):
        self._login_as_admin()

        target = User.objects.create_user(username="to_deactivate", password="Temp12345", is_active=True)
        target.groups.add(Group.objects.get(name="consulta"))
        profile = target.profile
        profile.role = "consulta"
        profile.must_change_password = False
        profile.save()

        deactivate_response = self.client.patch(
            reverse("admin-user-detail", args=[target.id]),
            {"is_active": False},
            format="json",
        )
        self.assertEqual(deactivate_response.status_code, status.HTTP_200_OK)

        self.client.credentials()
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "to_deactivate", "password": "Temp12345"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(login_response.data["code"], "USER_INACTIVE")

    def test_deactivating_already_inactive_user_does_not_duplicate_audit_log(self):
        self._login_as_admin()

        target = User.objects.create_user(username="already_inactive", password="Temp12345", is_active=False)
        target.groups.add(Group.objects.get(name="consulta"))
        profile = target.profile
        profile.role = "consulta"
        profile.must_change_password = False
        profile.save()

        response = self.client.patch(
            reverse("admin-user-detail", args=[target.id]),
            {"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AdministrativeActionLog.objects.filter(action="deactivate_user", target_user=target).count(), 0)

    def test_admin_can_reset_password_and_force_change(self):
        self._login_as_admin()

        target = User.objects.create_user(username="reset_user", password="OldTemp123", is_active=True)
        target.groups.add(Group.objects.get(name="reviewer"))
        profile = target.profile
        profile.role = "reviewer"
        profile.must_change_password = False
        profile.save()

        response = self.client.post(
            reverse("admin-user-reset-password", args=[target.id]),
            {"temporary_password": "NewTemp12345"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        target.refresh_from_db()
        self.assertTrue(target.profile.must_change_password)
        self.assertTrue(target.check_password("NewTemp12345"))
        self.assertEqual(AdministrativeActionLog.objects.filter(action="reset_password", target_user=target).count(), 1)

    def test_admin_can_list_audit_log(self):
        self._login_as_admin()

        target = User.objects.create_user(username="audit_user", password="Temp12345", is_active=True)
        target.groups.add(Group.objects.get(name="consulta"))
        profile = target.profile
        profile.role = "consulta"
        profile.must_change_password = False
        profile.save()
        AdministrativeActionLog.objects.create(
            action="create_user",
            target_user=target,
            performed_by=self.admin_user,
            details={"role": "consulta"},
        )

        response = self.client.get(reverse("admin-audit-log"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["target_username"], "audit_user")

    def test_reviewer_cannot_access_admin_user_management(self):
        self._login_as_reviewer()

        response = self.client.get(reverse("admin-user-collection"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
