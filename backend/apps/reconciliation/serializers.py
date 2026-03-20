from rest_framework import serializers

from apps.catalog.models import ArticleCatalog

from .models import ReconciliationItemResult, ReconciliationItemReview, ReconciliationLotResult, ReconciliationRun


def resolve_article_catalog(lot_result):
    formula_version = getattr(lot_result, "formula_version", None)
    formula = getattr(formula_version, "formula", None)
    article = getattr(formula, "article", None)
    if article and article.active:
        return article

    return ArticleCatalog.objects.filter(
        codpro=lot_result.codpro,
        codder=lot_result.codder,
        active=True,
    ).first()


class ReconciliationRunRequestSerializer(serializers.Serializer):
    date_start = serializers.DateField()
    date_end = serializers.DateField()
    nf1 = serializers.CharField(max_length=9, required=False, allow_null=True, allow_blank=True)
    codpro = serializers.CharField(max_length=14, required=False, allow_null=True, allow_blank=True)
    codder = serializers.CharField(max_length=7, required=False, allow_null=True, allow_blank=True)
    chemical_code = serializers.CharField(max_length=14, required=False, allow_null=True, allow_blank=True)
    only_divergences = serializers.BooleanField(default=False)
    only_inconsistencies = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if attrs["date_start"] > attrs["date_end"]:
            raise serializers.ValidationError("date_start must be less than or equal to date_end.")
        if (attrs["date_end"] - attrs["date_start"]).days > 90:
            raise serializers.ValidationError("Date window must be 90 days or less.")
        return attrs


class ReconciliationRunResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReconciliationRun
        fields = ("id", "processed_lots", "processed_items", "status", "error_message")


class ReconciliationRunListQuerySerializer(serializers.Serializer):
    status = serializers.CharField(max_length=20, required=False, allow_blank=True)
    date_start = serializers.DateField(required=False)
    date_end = serializers.DateField(required=False)
    executed_by = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate(self, attrs):
        date_start = attrs.get("date_start")
        date_end = attrs.get("date_end")
        if date_start and date_end and date_start > date_end:
            raise serializers.ValidationError("date_start must be less than or equal to date_end.")
        return attrs


class ReconciliationRunListSerializer(serializers.ModelSerializer):
    executed_by_username = serializers.CharField(source="executed_by.username", read_only=True)

    class Meta:
        model = ReconciliationRun
        fields = (
            "id",
            "executed_at",
            "executed_by_username",
            "date_start",
            "date_end",
            "processed_lots",
            "processed_items",
            "status",
            "error_message",
        )


class ReconciliationLotSummarySerializer(serializers.ModelSerializer):
    formula_version_number = serializers.IntegerField(source="formula_version.version_number", read_only=True)
    article_description = serializers.SerializerMethodField()
    derivation_description = serializers.SerializerMethodField()

    class Meta:
        model = ReconciliationLotResult
        fields = (
            "id",
            "nf1",
            "recurtimento_date",
            "codpro",
            "codder",
            "article_description",
            "derivation_description",
            "lot_weight",
            "formula_version_number",
            "status_final",
            "has_inconsistency",
            "has_divergence",
            "items_count",
        )

    def get_article_description(self, obj):
        article = resolve_article_catalog(obj)
        return article.article_description if article else None

    def get_derivation_description(self, obj):
        article = resolve_article_catalog(obj)
        return article.derivation_description if article else None


class ReconciliationRunDetailSerializer(serializers.ModelSerializer):
    executed_by_username = serializers.CharField(source="executed_by.username", read_only=True)
    lots = ReconciliationLotSummarySerializer(many=True, read_only=True)

    class Meta:
        model = ReconciliationRun
        fields = (
            "id",
            "executed_at",
            "executed_by_username",
            "date_start",
            "date_end",
            "nf1",
            "codpro",
            "codder",
            "chemical_code",
            "only_divergences",
            "only_inconsistencies",
            "processed_lots",
            "processed_items",
            "execution_time_ms",
            "status",
            "error_message",
            "lots",
        )


class ReconciliationItemReviewSerializer(serializers.ModelSerializer):
    reviewed_by_username = serializers.CharField(source="reviewed_by.username", read_only=True)

    class Meta:
        model = ReconciliationItemReview
        fields = (
            "id",
            "previous_status",
            "reviewed_status",
            "justification",
            "reviewed_by_username",
            "reviewed_at",
        )


class ReconciliationItemReviewCreateSerializer(serializers.Serializer):
    reviewed_status = serializers.ChoiceField(
        choices=(
            ReconciliationItemResult.STATUS_CONFORM,
            ReconciliationItemResult.STATUS_DIVERGENT,
            ReconciliationItemResult.STATUS_INCONSISTENT,
        )
    )
    justification = serializers.CharField(max_length=500)

    def validate_justification(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("justification is required.")
        return cleaned


class ReconciliationItemDetailSerializer(serializers.ModelSerializer):
    formula_version_number = serializers.IntegerField(source="formula_version.version_number", read_only=True)
    reviews = ReconciliationItemReviewSerializer(many=True, read_only=True)

    class Meta:
        model = ReconciliationItemResult
        fields = (
            "id",
            "nf1",
            "chemical_code",
            "chemical_description",
            "formula_version_number",
            "predicted_qty",
            "used_qty",
            "deviation_pct",
            "tolerance_pct",
            "status_calculated",
            "status_reviewed",
            "status_final",
            "inconsistency_code",
            "inconsistency_message",
            "reviews",
        )


class ReconciliationLotDetailSerializer(serializers.ModelSerializer):
    formula_version_number = serializers.IntegerField(source="formula_version.version_number", read_only=True)
    article_description = serializers.SerializerMethodField()
    derivation_description = serializers.SerializerMethodField()
    items = ReconciliationItemDetailSerializer(many=True, read_only=True)

    class Meta:
        model = ReconciliationLotResult
        fields = (
            "id",
            "nf1",
            "recurtimento_date",
            "codpro",
            "codder",
            "article_description",
            "derivation_description",
            "lot_weight",
            "formula_version_number",
            "status_final",
            "has_inconsistency",
            "has_divergence",
            "items_count",
            "items",
        )

    def get_article_description(self, obj):
        article = resolve_article_catalog(obj)
        return article.article_description if article else None

    def get_derivation_description(self, obj):
        article = resolve_article_catalog(obj)
        return article.derivation_description if article else None


class ReconciliationItemWithReviewsSerializer(serializers.ModelSerializer):
    formula_version_number = serializers.IntegerField(source="formula_version.version_number", read_only=True)
    reviews = ReconciliationItemReviewSerializer(many=True, read_only=True)

    class Meta:
        model = ReconciliationItemResult
        fields = (
            "id",
            "nf1",
            "chemical_code",
            "chemical_description",
            "formula_version_number",
            "predicted_qty",
            "used_qty",
            "deviation_pct",
            "tolerance_pct",
            "status_calculated",
            "status_reviewed",
            "status_final",
            "inconsistency_code",
            "inconsistency_message",
            "reviews",
        )
