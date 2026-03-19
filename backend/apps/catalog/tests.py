import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ArticleCatalog, ChemicalProductCatalog, SyncJobRun
from .oracle_adapter import OracleSyncError
from .services import sync_catalogs


class FakeAdapter:
    def fetch_articles(self):
        ts = now()
        return [
            {
                "codpro": "ART001",
                "codder": "00001",
                "article_description": "Artigo 1",
                "derivation_description": "Derivacao 1",
                "source_last_seen_at": ts,
            }
        ]

    def fetch_chemicals(self):
        ts = now()
        return [
            {
                "chemical_code": "QUI001",
                "description": "Quimico 1",
                "complement": "",
                "family_code": "F1",
                "unit_of_measure": "KG",
                "product_type": "PQ",
                "product_type_description": "Produto",
                "source_status": "A",
                "active": True,
                "source_last_seen_at": ts,
            }
        ]


class ErrorAdapter:
    def fetch_articles(self):
        raise OracleSyncError("timeout on articles query")

    def fetch_chemicals(self):
        return []


class CatalogSyncServiceTests(TestCase):
    def test_sync_catalogs_success(self):
        sync_run = sync_catalogs(adapter=FakeAdapter())
        self.assertEqual(sync_run.status, SyncJobRun.STATUS_SUCCESS)
        self.assertEqual(ArticleCatalog.objects.count(), 1)
        self.assertEqual(ChemicalProductCatalog.objects.count(), 1)

    def test_sync_catalogs_is_idempotent(self):
        sync_catalogs(adapter=FakeAdapter())
        sync_catalogs(adapter=FakeAdapter())
        self.assertEqual(ArticleCatalog.objects.count(), 1)
        self.assertEqual(ChemicalProductCatalog.objects.count(), 1)

    def test_sync_catalogs_failure(self):
        with self.assertRaises(OracleSyncError):
            sync_catalogs(adapter=ErrorAdapter())
        self.assertEqual(SyncJobRun.objects.first().status, SyncJobRun.STATUS_ERROR)


class CatalogApiTests(APITestCase):
    def setUp(self):
        for group_name in ("admin", "reviewer", "consulta"):
            Group.objects.get_or_create(name=group_name)
        self.user = User.objects.create_user(username="reviewer_catalog", password="Temp12345")
        self.user.groups.add(Group.objects.get(name="reviewer"))
        profile = self.user.profile
        profile.role = "reviewer"
        profile.must_change_password = False
        profile.save()
        login = self.client.post(
            reverse("auth-login"),
            {"username": "reviewer_catalog", "password": "Temp12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['data']['access']}")

    def test_catalog_endpoints_return_data(self):
        sync_catalogs(adapter=FakeAdapter())
        articles = self.client.get(reverse("catalog-articles"))
        chemicals = self.client.get(reverse("catalog-chemicals"))
        runs = self.client.get(reverse("sync-run-list"))
        self.assertEqual(articles.status_code, status.HTTP_200_OK)
        self.assertEqual(chemicals.status_code, status.HTTP_200_OK)
        self.assertEqual(runs.status_code, status.HTTP_200_OK)


class CatalogCommandTests(TestCase):
    def test_sync_catalogs_command_json(self):
        fixture_path = Path(settings.BASE_DIR) / "tmp_test_data" / "oracle_fixture.json"
        fixture_path.parent.mkdir(exist_ok=True)
        fixture_path.write_text(
            json.dumps(
                {
                    "articles": [
                        {
                            "codpro": "ART010",
                            "codder": "00010",
                            "article_description": "Artigo fixture",
                            "derivation_description": "Derivacao fixture",
                            "source_last_seen_at": now().isoformat(),
                        }
                    ],
                    "chemicals": [
                        {
                            "chemical_code": "QUI010",
                            "description": "Quimico fixture",
                            "complement": "",
                            "family_code": "F1",
                            "unit_of_measure": "KG",
                            "product_type": "PQ",
                            "product_type_description": "Produto",
                            "source_status": "A",
                            "active": True,
                            "source_last_seen_at": now().isoformat(),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        with override_settings():
            import os
            from io import StringIO

            os.environ["ORACLE_FIXTURE_PATH"] = str(fixture_path)
            out = StringIO()
            call_command("sync_catalogs", "--format=json", stdout=out)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["status"], "success")
            fixture_path.unlink(missing_ok=True)
