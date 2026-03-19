from rest_framework import serializers

from .models import ArticleCatalog, ChemicalProductCatalog, SyncJobRun


class ArticleCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleCatalog
        fields = "__all__"


class ChemicalProductCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChemicalProductCatalog
        fields = "__all__"


class SyncJobRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncJobRun
        fields = "__all__"
