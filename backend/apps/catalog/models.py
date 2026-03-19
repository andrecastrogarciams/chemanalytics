from django.db import models


class ActiveModel(models.Model):
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ArticleCatalog(ActiveModel):
    codpro = models.CharField(max_length=14)
    codder = models.CharField(max_length=7)
    article_description = models.CharField(max_length=100)
    derivation_description = models.CharField(max_length=50)
    source_last_seen_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["codpro", "codder"], name="uniq_article_catalog"),
        ]
        ordering = ["codpro", "codder"]


class ChemicalProductCatalog(ActiveModel):
    chemical_code = models.CharField(max_length=14, unique=True)
    description = models.CharField(max_length=100)
    complement = models.CharField(max_length=50, blank=True, null=True)
    family_code = models.CharField(max_length=6, blank=True, null=True)
    unit_of_measure = models.CharField(max_length=3, blank=True, null=True)
    product_type = models.CharField(max_length=2, blank=True, null=True)
    product_type_description = models.CharField(max_length=15, blank=True, null=True)
    source_status = models.CharField(max_length=5, blank=True, null=True)
    source_last_seen_at = models.DateTimeField()

    class Meta:
        ordering = ["chemical_code"]


class SyncJobRun(models.Model):
    JOB_AUTOMATIC = "automatic"
    JOB_MANUAL = "manual"
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"

    job_type = models.CharField(max_length=30, default=JOB_MANUAL)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, default=STATUS_RUNNING)
    records_articles_upserted = models.IntegerField(default=0)
    records_products_upserted = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    triggered_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-started_at"]
