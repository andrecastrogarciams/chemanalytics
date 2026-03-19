from django.conf import settings
from django.db import models

from apps.formulas.models import FormulaItem, FormulaVersion


class ReconciliationRun(models.Model):
    STATUS_SUCCESS = "success"
    STATUS_PARTIAL_ERROR = "partial_error"
    STATUS_ERROR = "error"

    executed_at = models.DateTimeField()
    executed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    date_start = models.DateField()
    date_end = models.DateField()
    nf1 = models.CharField(max_length=9, blank=True, null=True)
    codpro = models.CharField(max_length=14, blank=True, null=True)
    codder = models.CharField(max_length=7, blank=True, null=True)
    chemical_code = models.CharField(max_length=14, blank=True, null=True)
    only_divergences = models.BooleanField(default=False)
    only_inconsistencies = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default=STATUS_SUCCESS)
    processed_lots = models.IntegerField(default=0)
    processed_items = models.IntegerField(default=0)
    execution_time_ms = models.IntegerField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-executed_at"]


class ReconciliationLotResult(models.Model):
    STATUS_CONFORM = "conform"
    STATUS_DIVERGENT = "divergent"
    STATUS_INCONSISTENT = "inconsistent"

    run = models.ForeignKey(ReconciliationRun, related_name="lots", on_delete=models.CASCADE)
    nf1 = models.CharField(max_length=9)
    recurtimento_date = models.DateField()
    codpro = models.CharField(max_length=14)
    codder = models.CharField(max_length=7)
    lot_weight = models.DecimalField(max_digits=12, decimal_places=2)
    formula_version = models.ForeignKey(FormulaVersion, blank=True, null=True, on_delete=models.SET_NULL)
    status_final = models.CharField(max_length=20)
    has_inconsistency = models.BooleanField(default=False)
    has_divergence = models.BooleanField(default=False)
    items_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["run", "nf1"], name="uniq_run_nf1"),
        ]
        ordering = ["nf1"]


class ReconciliationItemResult(models.Model):
    STATUS_CONFORM = "conform"
    STATUS_DIVERGENT = "divergent"
    STATUS_INCONSISTENT = "inconsistent"

    run = models.ForeignKey(ReconciliationRun, related_name="items", on_delete=models.CASCADE)
    lot_result = models.ForeignKey(ReconciliationLotResult, related_name="items", on_delete=models.CASCADE)
    nf1 = models.CharField(max_length=9)
    chemical_code = models.CharField(max_length=14)
    chemical_description = models.CharField(max_length=100, blank=True, null=True)
    formula_version = models.ForeignKey(FormulaVersion, blank=True, null=True, on_delete=models.SET_NULL)
    formula_item = models.ForeignKey(FormulaItem, blank=True, null=True, on_delete=models.SET_NULL)
    predicted_qty = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    used_qty = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    deviation_pct = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tolerance_pct = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status_calculated = models.CharField(max_length=20)
    status_reviewed = models.CharField(max_length=20, blank=True, null=True)
    status_final = models.CharField(max_length=20)
    inconsistency_code = models.CharField(max_length=50, blank=True, null=True)
    inconsistency_message = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["run", "nf1", "chemical_code"], name="uniq_run_nf1_chemical"),
        ]
        ordering = ["nf1", "chemical_code"]


class ReconciliationItemReview(models.Model):
    item_result = models.ForeignKey(ReconciliationItemResult, related_name="reviews", on_delete=models.CASCADE)
    previous_status = models.CharField(max_length=20)
    reviewed_status = models.CharField(max_length=20)
    justification = models.CharField(max_length=500)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reviewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["reviewed_at", "id"]
