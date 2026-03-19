from django.contrib import admin

from .models import ArticleCatalog, ChemicalProductCatalog, SyncJobRun


@admin.register(ArticleCatalog)
class ArticleCatalogAdmin(admin.ModelAdmin):
    list_display = ("codpro", "codder", "article_description", "active", "source_last_seen_at")
    search_fields = ("codpro", "codder", "article_description")


@admin.register(ChemicalProductCatalog)
class ChemicalProductCatalogAdmin(admin.ModelAdmin):
    list_display = ("chemical_code", "description", "active", "source_status", "source_last_seen_at")
    search_fields = ("chemical_code", "description")


@admin.register(SyncJobRun)
class SyncJobRunAdmin(admin.ModelAdmin):
    list_display = ("id", "job_type", "status", "started_at", "finished_at")
    list_filter = ("job_type", "status")
