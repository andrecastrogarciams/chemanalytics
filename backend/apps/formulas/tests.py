import json
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import ArticleCatalog

from .models import Formula, FormulaItem, FormulaVersion


class FormulaModelTests(TestCase):
    def test_formula_unique_codpro_codder(self):
        Formula.objects.create(codpro="ART001", codder="D1")
        with self.assertRaises(IntegrityError):
            Formula.objects.create(codpro="ART001", codder="D1")

    def test_new_open_version_closes_previous_version(self):
        formula = Formula.objects.create(codpro="ART001", codder="D1")
        first = FormulaVersion.objects.create(formula=formula, version_number=1, start_date="2026-01-01")
        second = FormulaVersion.objects.create(formula=formula, version_number=2, start_date="2026-02-01")

        first.refresh_from_db()
        self.assertEqual(str(first.end_date), "2026-01-31")
        self.assertIsNone(second.end_date)

    def test_overlapping_versions_are_blocked(self):
        formula = Formula.objects.create(codpro="ART001", codder="D1")
        FormulaVersion.objects.create(
            formula=formula,
            version_number=1,
            start_date="2026-01-01",
            end_date="2026-01-31",
        )
        version = FormulaVersion(
            formula=formula,
            version_number=2,
            start_date="2026-01-15",
            end_date="2026-02-15",
        )
        with self.assertRaises(ValidationError):
            version.full_clean()

    def test_duplicate_chemical_in_same_version_is_blocked(self):
        formula = Formula.objects.create(codpro="ART001", codder="D1")
        version = FormulaVersion.objects.create(formula=formula, version_number=1, start_date="2026-01-01")
        FormulaItem.objects.create(
            formula_version=version,
            chemical_code="Q001",
            chemical_description="Acido",
            percentual="4.7000",
            tolerance_pct="2.00",
        )
        with self.assertRaises(ValidationError):
            FormulaItem.objects.create(
                formula_version=version,
                chemical_code="Q001",
                chemical_description="Acido",
                percentual="4.7000",
                tolerance_pct="2.00",
            )

    def test_incomplete_item_requires_reason_and_no_percentual(self):
        formula = Formula.objects.create(codpro="ART001", codder="D1")
        version = FormulaVersion.objects.create(formula=formula, version_number=1, start_date="2026-01-01")
        item = FormulaItem(
            formula_version=version,
            chemical_code="Q099",
            chemical_description="Incomplete",
            percentual=None,
            tolerance_pct="0.00",
            is_incomplete=True,
            incomplete_reason="Missing percentual in source file",
        )
        item.full_clean()


class FormulaBootstrapTests(TestCase):
    def test_bootstrap_command_imports_and_reports(self):
        csv_content = """codpro,codder,start_date,chemical_code,chemical_description,percentual,tolerance_pct
ART001,D1,2026-01-01,Q001,Acido,4.7000,2.00
ART001,D1,2026-01-01,Q002,Corante,1.2000,1.50
ART001,D1,2026-01-01,Q002,Corante,1.2000,1.50
ART002,D2,2026-02-01,Q010,Base,2.5000,0.50
"""
        temp_dir = Path(settings.BASE_DIR) / "tmp_test_data"
        temp_dir.mkdir(exist_ok=True)
        csv_path = temp_dir / "bootstrap.csv"
        csv_path.write_text(csv_content, encoding="utf-8")
        out = __import__("io").StringIO()

        call_command("bootstrap_formulas", str(csv_path), "--format=json", stdout=out)
        payload = json.loads(out.getvalue())
        csv_path.unlink(missing_ok=True)

        self.assertEqual(payload["source_type"], "csv")
        self.assertEqual(payload["formulas_created"], 2)
        self.assertEqual(payload["versions_created"], 2)
        self.assertEqual(payload["items_created"], 3)
        self.assertEqual(payload["incomplete_items_created"], 0)
        self.assertEqual(len(payload["rejected_rows"]), 1)


class FormulaApiTests(APITestCase):
    def setUp(self):
        for group_name in ("admin", "reviewer", "consulta"):
            Group.objects.get_or_create(name=group_name)

        self.admin = User.objects.create_user(username="formula_admin", password="Temp12345")
        self.admin.groups.add(Group.objects.get(name="admin"))
        profile = self.admin.profile
        profile.role = "admin"
        profile.must_change_password = False
        profile.save()

        login = self.client.post(
            reverse("auth-login"),
            {"username": "formula_admin", "password": "Temp12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['data']['access']}")

    def test_create_formula_with_initial_version(self):
        ArticleCatalog.objects.create(
            codpro="ART100",
            codder="D1",
            article_description="Artigo 100",
            derivation_description="Derivacao 1",
            source_last_seen_at=now(),
        )
        response = self.client.post(
            reverse("formula-list-create"),
            {
                "codpro": "ART100",
                "codder": "D1",
                "observation": "Initial formula",
                "start_date": "2026-01-01",
                "version_observation": "v1",
                "items": [
                    {
                        "chemical_code": "Q001",
                        "chemical_description": "Acido",
                        "percentual": "4.7000",
                        "tolerance_pct": "2.00",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["current_version"]["version_number"], 1)
        self.assertEqual(response.data["data"]["article_description"], "Artigo 100")
        self.assertEqual(response.data["data"]["derivation_description"], "Derivacao 1")

    def test_create_formula_requires_article_from_catalog(self):
        response = self.client.post(
            reverse("formula-list-create"),
            {
                "codpro": "ART404",
                "codder": "D9",
                "observation": "Missing article",
                "start_date": "2026-01-01",
                "version_observation": "v1",
                "items": [
                    {
                        "chemical_code": "Q001",
                        "chemical_description": "Acido",
                        "percentual": "4.7000",
                        "tolerance_pct": "2.00",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_new_version_closes_previous_one(self):
        formula = Formula.objects.create(codpro="ART100", codder="D1")
        first = FormulaVersion.objects.create(formula=formula, version_number=1, start_date="2026-01-01")
        FormulaItem.objects.create(
            formula_version=first,
            chemical_code="Q001",
            chemical_description="Acido",
            percentual="4.7000",
            tolerance_pct="2.00",
        )

        response = self.client.post(
            reverse("formula-version-create", kwargs={"formula_id": formula.id}),
            {
                "start_date": "2026-02-01",
                "observation": "v2",
                "items": [
                    {
                        "chemical_code": "Q002",
                        "chemical_description": "Corante",
                        "percentual": "1.2000",
                        "tolerance_pct": "1.00",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        first.refresh_from_db()
        self.assertEqual(str(first.end_date), "2026-01-31")

    def test_edit_unused_version_is_allowed(self):
        formula = Formula.objects.create(codpro="ART100", codder="D1")
        version = FormulaVersion.objects.create(formula=formula, version_number=1, start_date="2026-01-01")
        FormulaItem.objects.create(
            formula_version=version,
            chemical_code="Q001",
            chemical_description="Acido",
            percentual="4.7000",
            tolerance_pct="2.00",
        )

        response = self.client.patch(
            reverse("formula-version-update", kwargs={"version_id": version.id}),
            {
                "observation": "updated",
                "items": [
                    {
                        "chemical_code": "Q003",
                        "chemical_description": "Novo item",
                        "percentual": "2.5000",
                        "tolerance_pct": "1.50",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        version.refresh_from_db()
        self.assertEqual(version.observation, "updated")
        self.assertEqual(version.items.count(), 1)

    def test_edit_used_version_is_blocked(self):
        formula = Formula.objects.create(codpro="ART100", codder="D1")
        version = FormulaVersion.objects.create(
            formula=formula,
            version_number=1,
            start_date="2026-01-01",
            used_in_reconciliation=True,
        )

        response = self.client.patch(
            reverse("formula-version-update", kwargs={"version_id": version.id}),
            {"observation": "blocked"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_formula_detail_returns_version_history(self):
        formula = Formula.objects.create(codpro="ART100", codder="D1")
        FormulaVersion.objects.create(formula=formula, version_number=1, start_date="2026-01-01")
        FormulaVersion.objects.create(formula=formula, version_number=2, start_date="2026-02-01")

        response = self.client.get(reverse("formula-detail", kwargs={"formula_id": formula.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]["versions"]), 2)
