import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import ChemicalProductCatalog
from apps.formulas.models import Formula, FormulaItem, FormulaVersion

from .models import ReconciliationItemResult, ReconciliationLotResult, ReconciliationRun
from .models import ReconciliationItemReview
from .services import calculate_deviation_pct, calculate_predicted_qty


class ReconciliationMathTests(TestCase):
    def test_predicted_qty_rounding(self):
        self.assertEqual(str(calculate_predicted_qty("100.00", "4.7")), "4.70")

    def test_deviation_pct_rounding(self):
        self.assertEqual(str(calculate_deviation_pct("5.00", "4.70")), "6.38")


class ReconciliationApiTests(APITestCase):
    def setUp(self):
        for group_name in ("admin", "reviewer", "consulta"):
            Group.objects.get_or_create(name=group_name)
        self.user = User.objects.create_user(username="reviewer_recon", password="Temp12345")
        self.user.groups.add(Group.objects.get(name="reviewer"))
        profile = self.user.profile
        profile.role = "reviewer"
        profile.must_change_password = False
        profile.save()
        login = self.client.post(
            reverse("auth-login"),
            {"username": "reviewer_recon", "password": "Temp12345"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['data']['access']}")

        formula = Formula.objects.create(codpro="ART001", codder="00001")
        version = FormulaVersion.objects.create(formula=formula, version_number=1, start_date="2023-01-01")
        FormulaItem.objects.create(
            formula_version=version,
            chemical_code="QUI001",
            chemical_description="Acido",
            percentual="4.7000",
            tolerance_pct="2.00",
        )
        ChemicalProductCatalog.objects.create(
            chemical_code="QUI001",
            description="Acido",
            source_last_seen_at=now(),
        )

        fixture_dir = Path(settings.BASE_DIR) / "backend" / "apps" / "reconciliation" / "fixtures"
        fixture_dir.mkdir(parents=True, exist_ok=True)
        self.fixture_path = fixture_dir / "oracle_reconciliation_fixture.json"
        self.fixture_path.write_text(
            json.dumps(
                {
                    "lots": [
                        {
                            "nf1": "NF100",
                            "data": "2023-01-10",
                            "codpro": "ART001",
                            "codder": "00001",
                            "peso": "100.00",
                        },
                        {
                            "nf1": "NF200",
                            "data": "2023-01-10",
                            "codpro": "ART404",
                            "codder": "00001",
                            "peso": "80.00",
                        },
                    ],
                    "usages": [
                        {
                            "nf1": "NF100",
                            "codpro": "QUI001",
                            "despro": "Acido",
                            "qtduti": "5.00",
                        },
                        {
                            "nf1": "NF200",
                            "codpro": "QUI404",
                            "despro": "Inexistente",
                            "qtduti": "1.00",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

    def _authenticate(self, username, role, password="Temp12345"):
        user = User.objects.create_user(username=username, password=password)
        user.groups.add(Group.objects.get(name=role))
        profile = user.profile
        profile.role = role
        profile.must_change_password = False
        profile.save()
        login = self.client.post(
            reverse("auth-login"),
            {"username": username, "password": password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['data']['access']}")
        return user

    def tearDown(self):
        self.fixture_path.unlink(missing_ok=True)

    def test_reconciliation_run_success_and_persists_history(self):
        import os
        os.environ["ORACLE_RECONCILIATION_FIXTURE_PATH"] = str(self.fixture_path)

        response = self.client.post(
            reverse("reconciliation-run-collection"),
            {"date_start": "2023-01-01", "date_end": "2023-01-31"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReconciliationRun.objects.count(), 1)
        self.assertEqual(ReconciliationLotResult.objects.count(), 2)
        self.assertGreaterEqual(ReconciliationItemResult.objects.count(), 2)
        first_item = ReconciliationItemResult.objects.filter(nf1="NF100", chemical_code="QUI001").first()
        self.assertEqual(str(first_item.predicted_qty), "4.70")
        self.assertEqual(first_item.status_final, ReconciliationItemResult.STATUS_DIVERGENT)
        missing_formula = ReconciliationItemResult.objects.filter(nf1="NF200").first()
        self.assertEqual(missing_formula.inconsistency_code, "formula_not_found")

    def test_reconciliation_fails_when_oracle_unavailable(self):
        import os
        os.environ.pop("ORACLE_RECONCILIATION_FIXTURE_PATH", None)
        response = self.client.post(
            reverse("reconciliation-run-collection"),
            {"date_start": "2023-01-01", "date_end": "2023-01-31"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_consulta_can_list_run_history_and_filter(self):
        run = ReconciliationRun.objects.create(
            executed_at=now(),
            executed_by=self.user,
            date_start="2023-01-01",
            date_end="2023-01-31",
            processed_lots=2,
            processed_items=4,
            status=ReconciliationRun.STATUS_SUCCESS,
        )
        ReconciliationRun.objects.create(
            executed_at=now(),
            executed_by=self.user,
            date_start="2023-02-01",
            date_end="2023-02-28",
            processed_lots=1,
            processed_items=1,
            status=ReconciliationRun.STATUS_ERROR,
            error_message="oracle timeout",
        )

        self._authenticate("consulta_recon", "consulta")
        response = self.client.get(
            reverse("reconciliation-run-collection"),
            {"status": ReconciliationRun.STATUS_SUCCESS},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["id"], run.id)
        self.assertEqual(response.data["data"][0]["executed_by_username"], self.user.username)

    def test_run_detail_returns_lot_summary_from_frozen_history(self):
        run = ReconciliationRun.objects.create(
            executed_at=now(),
            executed_by=self.user,
            date_start="2023-01-01",
            date_end="2023-01-31",
            processed_lots=1,
            processed_items=1,
            status=ReconciliationRun.STATUS_SUCCESS,
        )
        lot = ReconciliationLotResult.objects.create(
            run=run,
            nf1="NF100",
            recurtimento_date="2023-01-10",
            codpro="ART001",
            codder="00001",
            lot_weight="100.00",
            formula_version=FormulaVersion.objects.first(),
            status_final=ReconciliationLotResult.STATUS_DIVERGENT,
            has_divergence=True,
            items_count=1,
        )

        self._authenticate("consulta_detail", "consulta")
        response = self.client.get(reverse("reconciliation-run-detail", args=[run.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], run.id)
        self.assertEqual(len(response.data["data"]["lots"]), 1)
        self.assertEqual(response.data["data"]["lots"][0]["id"], lot.id)
        self.assertTrue(response.data["data"]["lots"][0]["has_divergence"])

    def test_lot_detail_returns_items_and_highlights_inconsistency(self):
        run = ReconciliationRun.objects.create(
            executed_at=now(),
            executed_by=self.user,
            date_start="2023-01-01",
            date_end="2023-01-31",
            processed_lots=1,
            processed_items=1,
            status=ReconciliationRun.STATUS_SUCCESS,
        )
        lot = ReconciliationLotResult.objects.create(
            run=run,
            nf1="NF200",
            recurtimento_date="2023-01-10",
            codpro="ART404",
            codder="00001",
            lot_weight="80.00",
            status_final=ReconciliationLotResult.STATUS_INCONSISTENT,
            has_inconsistency=True,
            items_count=1,
        )
        item = ReconciliationItemResult.objects.create(
            run=run,
            lot_result=lot,
            nf1="NF200",
            chemical_code="QUI404",
            chemical_description="Inexistente",
            status_calculated=ReconciliationItemResult.STATUS_INCONSISTENT,
            status_final=ReconciliationItemResult.STATUS_INCONSISTENT,
            inconsistency_code="formula_not_found",
            inconsistency_message="No formula version found for lot date.",
        )

        self._authenticate("consulta_lot", "consulta")
        response = self.client.get(reverse("reconciliation-lot-detail", args=[lot.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id"], lot.id)
        self.assertTrue(response.data["data"]["has_inconsistency"])
        self.assertEqual(len(response.data["data"]["items"]), 1)
        self.assertEqual(response.data["data"]["items"][0]["id"], item.id)
        self.assertEqual(response.data["data"]["items"][0]["inconsistency_code"], "formula_not_found")

    def test_anonymous_user_cannot_list_history(self):
        self.client.credentials()
        response = self.client.get(reverse("reconciliation-run-collection"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reviewer_can_create_manual_review_with_justification(self):
        run = ReconciliationRun.objects.create(
            executed_at=now(),
            executed_by=self.user,
            date_start="2023-01-01",
            date_end="2023-01-31",
            processed_lots=1,
            processed_items=1,
            status=ReconciliationRun.STATUS_SUCCESS,
        )
        lot = ReconciliationLotResult.objects.create(
            run=run,
            nf1="NF100",
            recurtimento_date="2023-01-10",
            codpro="ART001",
            codder="00001",
            lot_weight="100.00",
            status_final=ReconciliationLotResult.STATUS_DIVERGENT,
            has_divergence=True,
            items_count=1,
        )
        item = ReconciliationItemResult.objects.create(
            run=run,
            lot_result=lot,
            nf1="NF100",
            chemical_code="QUI001",
            chemical_description="Acido",
            predicted_qty="4.70",
            used_qty="5.00",
            deviation_pct="6.38",
            tolerance_pct="2.00",
            status_calculated=ReconciliationItemResult.STATUS_DIVERGENT,
            status_final=ReconciliationItemResult.STATUS_DIVERGENT,
        )

        response = self.client.post(
            reverse("reconciliation-item-review-create", args=[item.id]),
            {"reviewed_status": ReconciliationItemResult.STATUS_CONFORM, "justification": "Ajuste operacional aprovado."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item.refresh_from_db()
        lot.refresh_from_db()
        self.assertEqual(item.status_reviewed, ReconciliationItemResult.STATUS_CONFORM)
        self.assertEqual(item.status_final, ReconciliationItemResult.STATUS_CONFORM)
        self.assertEqual(lot.status_final, ReconciliationLotResult.STATUS_CONFORM)
        self.assertEqual(ReconciliationItemReview.objects.count(), 1)
        self.assertEqual(ReconciliationItemReview.objects.first().previous_status, ReconciliationItemResult.STATUS_DIVERGENT)
        self.assertEqual(response.data["data"]["reviews"][0]["justification"], "Ajuste operacional aprovado.")

    def test_manual_review_requires_justification(self):
        run = ReconciliationRun.objects.create(
            executed_at=now(),
            executed_by=self.user,
            date_start="2023-01-01",
            date_end="2023-01-31",
            processed_lots=1,
            processed_items=1,
            status=ReconciliationRun.STATUS_SUCCESS,
        )
        lot = ReconciliationLotResult.objects.create(
            run=run,
            nf1="NF100",
            recurtimento_date="2023-01-10",
            codpro="ART001",
            codder="00001",
            lot_weight="100.00",
            status_final=ReconciliationLotResult.STATUS_DIVERGENT,
            has_divergence=True,
            items_count=1,
        )
        item = ReconciliationItemResult.objects.create(
            run=run,
            lot_result=lot,
            nf1="NF100",
            chemical_code="QUI001",
            status_calculated=ReconciliationItemResult.STATUS_DIVERGENT,
            status_final=ReconciliationItemResult.STATUS_DIVERGENT,
        )

        response = self.client.post(
            reverse("reconciliation-item-review-create", args=[item.id]),
            {"reviewed_status": ReconciliationItemResult.STATUS_CONFORM, "justification": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ReconciliationItemReview.objects.count(), 0)

    def test_consulta_cannot_create_manual_review(self):
        run = ReconciliationRun.objects.create(
            executed_at=now(),
            executed_by=self.user,
            date_start="2023-01-01",
            date_end="2023-01-31",
            processed_lots=1,
            processed_items=1,
            status=ReconciliationRun.STATUS_SUCCESS,
        )
        lot = ReconciliationLotResult.objects.create(
            run=run,
            nf1="NF100",
            recurtimento_date="2023-01-10",
            codpro="ART001",
            codder="00001",
            lot_weight="100.00",
            status_final=ReconciliationLotResult.STATUS_DIVERGENT,
            has_divergence=True,
            items_count=1,
        )
        item = ReconciliationItemResult.objects.create(
            run=run,
            lot_result=lot,
            nf1="NF100",
            chemical_code="QUI001",
            status_calculated=ReconciliationItemResult.STATUS_DIVERGENT,
            status_final=ReconciliationItemResult.STATUS_DIVERGENT,
        )

        self._authenticate("consulta_review", "consulta")
        response = self.client.post(
            reverse("reconciliation-item-review-create", args=[item.id]),
            {"reviewed_status": ReconciliationItemResult.STATUS_CONFORM, "justification": "Nao autorizado."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ReconciliationItemReview.objects.count(), 0)

    def test_manual_review_keeps_immutable_audit_trail(self):
        run = ReconciliationRun.objects.create(
            executed_at=now(),
            executed_by=self.user,
            date_start="2023-01-01",
            date_end="2023-01-31",
            processed_lots=1,
            processed_items=1,
            status=ReconciliationRun.STATUS_SUCCESS,
        )
        lot = ReconciliationLotResult.objects.create(
            run=run,
            nf1="NF100",
            recurtimento_date="2023-01-10",
            codpro="ART001",
            codder="00001",
            lot_weight="100.00",
            status_final=ReconciliationLotResult.STATUS_DIVERGENT,
            has_divergence=True,
            items_count=1,
        )
        item = ReconciliationItemResult.objects.create(
            run=run,
            lot_result=lot,
            nf1="NF100",
            chemical_code="QUI001",
            status_calculated=ReconciliationItemResult.STATUS_DIVERGENT,
            status_final=ReconciliationItemResult.STATUS_DIVERGENT,
        )

        first = self.client.post(
            reverse("reconciliation-item-review-create", args=[item.id]),
            {"reviewed_status": ReconciliationItemResult.STATUS_CONFORM, "justification": "Primeira excecao."},
            format="json",
        )
        second = self.client.post(
            reverse("reconciliation-item-review-create", args=[item.id]),
            {"reviewed_status": ReconciliationItemResult.STATUS_INCONSISTENT, "justification": "Nova evidencia."},
            format="json",
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        item.refresh_from_db()
        reviews = list(ReconciliationItemReview.objects.filter(item_result=item).order_by("id"))
        self.assertEqual(len(reviews), 2)
        self.assertEqual(reviews[0].previous_status, ReconciliationItemResult.STATUS_DIVERGENT)
        self.assertEqual(reviews[0].reviewed_status, ReconciliationItemResult.STATUS_CONFORM)
        self.assertEqual(reviews[1].previous_status, ReconciliationItemResult.STATUS_CONFORM)
        self.assertEqual(reviews[1].reviewed_status, ReconciliationItemResult.STATUS_INCONSISTENT)
        self.assertEqual(item.status_final, ReconciliationItemResult.STATUS_INCONSISTENT)
