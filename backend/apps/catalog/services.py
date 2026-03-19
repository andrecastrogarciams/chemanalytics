import logging
from django.utils.timezone import now

from .models import ArticleCatalog, ChemicalProductCatalog, SyncJobRun
from .oracle_adapter import OracleCatalogAdapter, OracleSyncError


logger = logging.getLogger(__name__)


def sync_catalogs(job_type=SyncJobRun.JOB_MANUAL, triggered_by=None, adapter=None):
    adapter = adapter or OracleCatalogAdapter()
    sync_run = SyncJobRun.objects.create(
        job_type=job_type,
        started_at=now(),
        status=SyncJobRun.STATUS_RUNNING,
        triggered_by=triggered_by,
    )
    try:
        articles = adapter.fetch_articles()
        chemicals = adapter.fetch_chemicals()

        article_count = 0
        seen_articles = set()
        for item in articles:
            key = (item["codpro"], item["codder"])
            seen_articles.add(key)
            ArticleCatalog.objects.update_or_create(
                codpro=item["codpro"],
                codder=item["codder"],
                defaults={
                    "article_description": item["article_description"],
                    "derivation_description": item["derivation_description"],
                    "active": True,
                    "source_last_seen_at": item["source_last_seen_at"],
                },
            )
            article_count += 1
        ArticleCatalog.objects.exclude(
            pk__in=ArticleCatalog.objects.filter(
                codpro__in=[codpro for codpro, _ in seen_articles]
            ).values("pk")
        )

        chemical_count = 0
        seen_chemicals = set()
        for item in chemicals:
            seen_chemicals.add(item["chemical_code"])
            ChemicalProductCatalog.objects.update_or_create(
                chemical_code=item["chemical_code"],
                defaults={
                    "description": item["description"],
                    "complement": item.get("complement"),
                    "family_code": item.get("family_code"),
                    "unit_of_measure": item.get("unit_of_measure"),
                    "product_type": item.get("product_type"),
                    "product_type_description": item.get("product_type_description"),
                    "source_status": item.get("source_status"),
                    "active": item.get("active", True),
                    "source_last_seen_at": item["source_last_seen_at"],
                },
            )
            chemical_count += 1

        sync_run.records_articles_upserted = article_count
        sync_run.records_products_upserted = chemical_count
        sync_run.status = SyncJobRun.STATUS_SUCCESS
        sync_run.finished_at = now()
        sync_run.save()
        logger.info("sync_finished run_id=%s articles=%s chemicals=%s", sync_run.id, article_count, chemical_count)
        return sync_run
    except OracleSyncError as exc:
        sync_run.status = SyncJobRun.STATUS_ERROR
        sync_run.error_message = str(exc)
        sync_run.finished_at = now()
        sync_run.save()
        logger.error("sync_failed run_id=%s error=%s", sync_run.id, exc)
        raise
