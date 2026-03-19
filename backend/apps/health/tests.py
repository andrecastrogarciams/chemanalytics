import json

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import SyncJobRun


class HealthTests(APITestCase):
    def setUp(self):
        for group_name in ("admin", "reviewer", "consulta"):
            Group.objects.get_or_create(name=group_name)

        self.admin = User.objects.create_user(username="admin_user", password="Temp12345")
        self.admin_profile = self.admin.profile
        self.admin_profile.role = "admin"
        self.admin_profile.must_change_password = False
        self.admin_profile.save()

        self.reviewer = User.objects.create_user(username="review_user", password="Temp12345")
        self.reviewer_profile = self.reviewer.profile
        self.reviewer_profile.role = "reviewer"
        self.reviewer_profile.must_change_password = False
        self.reviewer_profile.save()

    def test_live_health_is_public(self):
        response = self.client.get(reverse("health-live"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")

    def test_dependencies_health_requires_admin(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "review_user", "password": "Temp12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")

        response = self.client.get(reverse("health-dependencies"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dependencies_health_for_admin(self):
        SyncJobRun.objects.create(
            job_type=SyncJobRun.JOB_MANUAL,
            started_at="2026-03-18T10:00:00Z",
            finished_at="2026-03-18T10:01:00Z",
            status=SyncJobRun.STATUS_SUCCESS,
            records_articles_upserted=10,
            records_products_upserted=20,
        )
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "admin_user", "password": "Temp12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")

        response = self.client.get(reverse("health-dependencies"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("database", response.data["dependencies"])
        self.assertIn("oracle", response.data["dependencies"])
        self.assertEqual(response.data["dependencies"]["last_sync"]["status"], "ok")

    def test_dependencies_health_is_degraded_when_last_sync_failed(self):
        SyncJobRun.objects.create(
            job_type=SyncJobRun.JOB_MANUAL,
            started_at="2026-03-18T10:00:00Z",
            finished_at="2026-03-18T10:01:00Z",
            status=SyncJobRun.STATUS_ERROR,
            error_message="oracle timeout",
        )
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "admin_user", "password": "Temp12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['data']['access']}")

        response = self.client.get(reverse("health-dependencies"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "degraded")
        self.assertEqual(response.data["dependencies"]["last_sync"]["status"], "error")

    def test_system_status_command_outputs_json(self):
        from io import StringIO

        out = StringIO()
        call_command("system_status", "--format=json", stdout=out)
        payload = json.loads(out.getvalue())

        self.assertEqual(payload["live"]["status"], "ok")
        self.assertIn("dependencies", payload["dependencies"])
