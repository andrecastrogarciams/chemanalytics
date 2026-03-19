from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction


class ActiveModel(models.Model):
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Formula(ActiveModel):
    codpro = models.CharField(max_length=14)
    codder = models.CharField(max_length=7)
    observation = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["codpro", "codder"], name="uniq_formula_codpro_codder"),
        ]
        ordering = ["codpro", "codder"]

    def __str__(self):
        return f"{self.codpro}/{self.codder}"


class FormulaVersion(ActiveModel):
    formula = models.ForeignKey(Formula, related_name="versions", on_delete=models.PROTECT)
    version_number = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    observation = models.TextField(blank=True, null=True)
    used_in_reconciliation = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["formula", "version_number"], name="uniq_formula_version_number"),
        ]
        indexes = [
            models.Index(fields=["formula", "start_date", "end_date"], name="idx_formula_validity"),
        ]
        ordering = ["formula_id", "-start_date", "-version_number"]

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "end_date must be greater than or equal to start_date."})

        overlapping = FormulaVersion.objects.filter(formula=self.formula).exclude(pk=self.pk)
        for version in overlapping:
            version_end = version.end_date or self.start_date
            current_end = self.end_date or version.start_date
            if self.start_date <= version_end and version.start_date <= current_end:
                raise ValidationError("Formula version validity overlaps with an existing version.")

    def save(self, *args, **kwargs):
        date_field = self._meta.get_field("start_date")
        self.start_date = date_field.to_python(self.start_date)
        if self.end_date is not None:
            self.end_date = self._meta.get_field("end_date").to_python(self.end_date)
        with transaction.atomic():
            previous_open = (
                FormulaVersion.objects.select_for_update()
                .filter(formula=self.formula, end_date__isnull=True)
                .exclude(pk=self.pk)
                .order_by("-start_date")
                .first()
            )
            if previous_open and previous_open.start_date < self.start_date:
                previous_open.end_date = self.start_date - timedelta(days=1)
                previous_open.save(update_fields=["end_date", "updated_at"])
            self.full_clean()
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.formula} v{self.version_number}"


class FormulaItem(ActiveModel):
    formula_version = models.ForeignKey(FormulaVersion, related_name="items", on_delete=models.PROTECT)
    chemical_code = models.CharField(max_length=14)
    chemical_description = models.CharField(max_length=100)
    percentual = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    tolerance_pct = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_incomplete = models.BooleanField(default=False)
    incomplete_reason = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["formula_version", "chemical_code"],
                name="uniq_formula_version_chemical",
            ),
        ]
        ordering = ["formula_version_id", "chemical_code"]

    def clean(self):
        if self.is_incomplete:
            if self.percentual not in (None, ""):
                raise ValidationError({"percentual": "Incomplete items must not define percentual."})
            if not self.incomplete_reason:
                raise ValidationError({"incomplete_reason": "Incomplete items require a reason."})
        else:
            if self.percentual is None or self.percentual <= 0:
                raise ValidationError({"percentual": "percentual must be greater than zero."})
        if self.tolerance_pct < 0:
            raise ValidationError({"tolerance_pct": "tolerance_pct must be greater than or equal to zero."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.chemical_code} ({self.percentual}%)"
