from django.db import transaction
from rest_framework import serializers

from apps.catalog.models import ArticleCatalog

from .models import Formula, FormulaItem, FormulaVersion


class FormulaItemInputSerializer(serializers.Serializer):
    chemical_code = serializers.CharField(max_length=14)
    chemical_description = serializers.CharField(max_length=100)
    percentual = serializers.DecimalField(max_digits=10, decimal_places=4, required=False, allow_null=True)
    tolerance_pct = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_incomplete = serializers.BooleanField(required=False, default=False)
    incomplete_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class FormulaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormulaItem
        fields = (
            "id",
            "chemical_code",
            "chemical_description",
            "percentual",
            "tolerance_pct",
            "is_incomplete",
            "incomplete_reason",
            "active",
        )


class FormulaVersionSerializer(serializers.ModelSerializer):
    items = FormulaItemSerializer(many=True, read_only=True)

    class Meta:
        model = FormulaVersion
        fields = (
            "id",
            "version_number",
            "start_date",
            "end_date",
            "observation",
            "active",
            "used_in_reconciliation",
            "items",
        )


class FormulaSerializer(serializers.ModelSerializer):
    versions = FormulaVersionSerializer(many=True, read_only=True)
    current_version = serializers.SerializerMethodField()
    article_description = serializers.CharField(source="article.article_description", read_only=True)
    derivation_description = serializers.CharField(source="article.derivation_description", read_only=True)

    class Meta:
        model = Formula
        fields = (
            "id",
            "codpro",
            "codder",
            "article_description",
            "derivation_description",
            "observation",
            "active",
            "current_version",
            "versions",
        )

    def get_current_version(self, obj):
        version = obj.versions.filter(active=True).order_by("-start_date", "-version_number").first()
        return FormulaVersionSerializer(version).data if version else None


class FormulaCreateSerializer(serializers.Serializer):
    codpro = serializers.CharField(max_length=14)
    codder = serializers.CharField(max_length=7)
    observation = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    start_date = serializers.DateField()
    version_observation = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    items = FormulaItemInputSerializer(many=True, min_length=1)

    def validate_items(self, items):
        codes = [item["chemical_code"] for item in items]
        if len(codes) != len(set(codes)):
            raise serializers.ValidationError("Duplicate chemical_code is not allowed in the same version.")
        return items

    def validate(self, attrs):
        article = ArticleCatalog.objects.filter(codpro=attrs["codpro"], codder=attrs["codder"], active=True).first()
        if not article:
            raise serializers.ValidationError("Article/derivation pair not found in synchronized Oracle catalog.")
        attrs["article"] = article
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items")
        start_date = validated_data.pop("start_date")
        version_observation = validated_data.pop("version_observation", None)
        formula = Formula.objects.create(**validated_data)
        version = FormulaVersion.objects.create(
            formula=formula,
            version_number=1,
            start_date=start_date,
            observation=version_observation,
        )
        for item in items:
            FormulaItem.objects.create(formula_version=version, **item)
        return formula


class FormulaVersionCreateSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    observation = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    items = FormulaItemInputSerializer(many=True, min_length=1)

    def validate_items(self, items):
        codes = [item["chemical_code"] for item in items]
        if len(codes) != len(set(codes)):
            raise serializers.ValidationError("Duplicate chemical_code is not allowed in the same version.")
        return items

    @transaction.atomic
    def create(self, validated_data):
        formula = self.context["formula"]
        items = validated_data.pop("items")
        latest = formula.versions.order_by("-version_number").first()
        next_version = (latest.version_number if latest else 0) + 1
        version = FormulaVersion.objects.create(
            formula=formula,
            version_number=next_version,
            start_date=validated_data["start_date"],
            observation=validated_data.get("observation"),
        )
        for item in items:
            FormulaItem.objects.create(formula_version=version, **item)
        return version


class FormulaVersionUpdateSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False, allow_null=True)
    observation = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    items = FormulaItemInputSerializer(many=True, min_length=1, required=False)

    def validate(self, attrs):
        version = self.context["version"]
        if version.used_in_reconciliation:
            raise serializers.ValidationError("Version already used in reconciliation and cannot be edited.")
        return attrs

    def validate_items(self, items):
        codes = [item["chemical_code"] for item in items]
        if len(codes) != len(set(codes)):
            raise serializers.ValidationError("Duplicate chemical_code is not allowed in the same version.")
        return items

    @transaction.atomic
    def save(self, **kwargs):
        version = self.context["version"]
        for field in ("start_date", "end_date", "observation"):
            if field in self.validated_data:
                setattr(version, field, self.validated_data[field])
        version.save()

        if "items" in self.validated_data:
            version.items.all().delete()
            for item in self.validated_data["items"]:
                FormulaItem.objects.create(formula_version=version, **item)

        return version
