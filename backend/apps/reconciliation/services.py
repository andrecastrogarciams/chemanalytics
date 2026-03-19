from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from time import perf_counter

from django.db import transaction
from django.db.models import Q
from django.utils.timezone import now

from apps.catalog.models import ChemicalProductCatalog
from apps.formulas.models import FormulaVersion

from .models import ReconciliationItemResult, ReconciliationLotResult, ReconciliationRun
from .oracle_adapter import OracleReconciliationAdapter, OracleReconciliationError


def round_decimal(value, places):
    quant = Decimal("1").scaleb(-places)
    return Decimal(value).quantize(quant, rounding=ROUND_HALF_UP)


def find_formula_version(codpro, codder, recurtimento_date):
    versions = FormulaVersion.objects.filter(
        formula__codpro=codpro,
        formula__codder=codder,
        start_date__lte=recurtimento_date,
    ).filter(Q(end_date__isnull=True) | Q(end_date__gte=recurtimento_date)).order_by("-start_date")

    count = versions.count()
    if count > 1:
        raise ValueError("More than one formula version matched the same date.")
    return versions.first()


def calculate_predicted_qty(lot_weight, percentual):
    return round_decimal(Decimal(lot_weight) * (Decimal(percentual) / Decimal("100")), 2)


def calculate_deviation_pct(used_qty, predicted_qty):
    predicted_decimal = Decimal(predicted_qty)
    return round_decimal(((Decimal(used_qty) - predicted_decimal) / predicted_decimal) * Decimal("100"), 2)


def derive_lot_status(items):
    if any(item["status_final"] == ReconciliationItemResult.STATUS_INCONSISTENT for item in items):
        return ReconciliationLotResult.STATUS_INCONSISTENT
    if any(item["status_final"] == ReconciliationItemResult.STATUS_DIVERGENT for item in items):
        return ReconciliationLotResult.STATUS_DIVERGENT
    return ReconciliationLotResult.STATUS_CONFORM


def build_item_result(chemical_code, lot, formula_version, formula_item, usage):
    if not formula_version:
        return {
            "chemical_code": chemical_code,
            "chemical_description": usage.get("despro") if usage else None,
            "formula_version": None,
            "formula_item": None,
            "predicted_qty": None,
            "used_qty": round_decimal(usage["qtduti"], 2) if usage else None,
            "deviation_pct": None,
            "tolerance_pct": None,
            "status_calculated": ReconciliationItemResult.STATUS_INCONSISTENT,
            "status_final": ReconciliationItemResult.STATUS_INCONSISTENT,
            "inconsistency_code": "formula_not_found",
            "inconsistency_message": "No formula version found for lot date.",
        }

    if usage and not formula_item:
        return {
            "chemical_code": chemical_code,
            "chemical_description": usage.get("despro"),
            "formula_version": formula_version,
            "formula_item": None,
            "predicted_qty": None,
            "used_qty": round_decimal(usage["qtduti"], 2),
            "deviation_pct": None,
            "tolerance_pct": None,
            "status_calculated": ReconciliationItemResult.STATUS_INCONSISTENT,
            "status_final": ReconciliationItemResult.STATUS_INCONSISTENT,
            "inconsistency_code": "chemical_not_in_formula",
            "inconsistency_message": "Chemical exists in Oracle usage but not in formula.",
        }

    if formula_item and formula_item.is_incomplete:
        return {
            "chemical_code": chemical_code,
            "chemical_description": formula_item.chemical_description,
            "formula_version": formula_version,
            "formula_item": formula_item,
            "predicted_qty": None,
            "used_qty": round_decimal(usage["qtduti"], 2) if usage else Decimal("0.00"),
            "deviation_pct": None,
            "tolerance_pct": formula_item.tolerance_pct,
            "status_calculated": ReconciliationItemResult.STATUS_INCONSISTENT,
            "status_final": ReconciliationItemResult.STATUS_INCONSISTENT,
            "inconsistency_code": "formula_item_incomplete",
            "inconsistency_message": formula_item.incomplete_reason or "Formula item is incomplete.",
        }

    if formula_item and not usage:
        return {
            "chemical_code": chemical_code,
            "chemical_description": formula_item.chemical_description,
            "formula_version": formula_version,
            "formula_item": formula_item,
            "predicted_qty": calculate_predicted_qty(lot["peso"], formula_item.percentual),
            "used_qty": Decimal("0.00"),
            "deviation_pct": None,
            "tolerance_pct": formula_item.tolerance_pct,
            "status_calculated": ReconciliationItemResult.STATUS_INCONSISTENT,
            "status_final": ReconciliationItemResult.STATUS_INCONSISTENT,
            "inconsistency_code": "formula_item_without_usage",
            "inconsistency_message": "Formula item has no Oracle usage.",
        }

    predicted_qty = calculate_predicted_qty(lot["peso"], formula_item.percentual)
    if predicted_qty <= 0:
        return {
            "chemical_code": chemical_code,
            "chemical_description": formula_item.chemical_description,
            "formula_version": formula_version,
            "formula_item": formula_item,
            "predicted_qty": predicted_qty,
            "used_qty": round_decimal(usage["qtduti"], 2),
            "deviation_pct": None,
            "tolerance_pct": formula_item.tolerance_pct,
            "status_calculated": ReconciliationItemResult.STATUS_INCONSISTENT,
            "status_final": ReconciliationItemResult.STATUS_INCONSISTENT,
            "inconsistency_code": "predicted_zero",
            "inconsistency_message": "Predicted quantity is zero.",
        }

    if not ChemicalProductCatalog.objects.filter(chemical_code=chemical_code, active=True).exists():
        return {
            "chemical_code": chemical_code,
            "chemical_description": formula_item.chemical_description,
            "formula_version": formula_version,
            "formula_item": formula_item,
            "predicted_qty": predicted_qty,
            "used_qty": round_decimal(usage["qtduti"], 2),
            "deviation_pct": None,
            "tolerance_pct": formula_item.tolerance_pct,
            "status_calculated": ReconciliationItemResult.STATUS_INCONSISTENT,
            "status_final": ReconciliationItemResult.STATUS_INCONSISTENT,
            "inconsistency_code": "inactive_or_stale_catalog_code",
            "inconsistency_message": "Chemical code not active in local catalog.",
        }

    used_qty = round_decimal(usage["qtduti"], 2)
    deviation_pct = calculate_deviation_pct(used_qty, predicted_qty)
    status = (
        ReconciliationItemResult.STATUS_CONFORM
        if abs(deviation_pct) <= formula_item.tolerance_pct
        else ReconciliationItemResult.STATUS_DIVERGENT
    )
    return {
        "chemical_code": chemical_code,
        "chemical_description": formula_item.chemical_description,
        "formula_version": formula_version,
        "formula_item": formula_item,
        "predicted_qty": predicted_qty,
        "used_qty": used_qty,
        "deviation_pct": deviation_pct,
        "tolerance_pct": formula_item.tolerance_pct,
        "status_calculated": status,
        "status_final": status,
        "inconsistency_code": None,
        "inconsistency_message": None,
    }


@transaction.atomic
def execute_reconciliation(validated_data, executed_by, adapter=None):
    adapter = adapter or OracleReconciliationAdapter()
    started = perf_counter()
    run = ReconciliationRun.objects.create(executed_at=now(), executed_by=executed_by, **validated_data)
    try:
        lots = adapter.fetch_lots(validated_data)
        usages = adapter.fetch_usages([lot["nf1"] for lot in lots])
        usages_by_nf1 = defaultdict(list)
        for usage in usages:
            usages_by_nf1[usage["nf1"]].append(usage)

        processed_items = 0
        used_versions = set()
        for lot in lots:
            formula_version = find_formula_version(lot["codpro"], lot["codder"], lot["data"])
            if formula_version:
                used_versions.add(formula_version.id)
                formula_items = {item.chemical_code: item for item in formula_version.items.filter(active=True)}
            else:
                formula_items = {}

            usage_map = {item["codpro"]: item for item in usages_by_nf1.get(lot["nf1"], [])}
            chemical_set = set(formula_items.keys()) | set(usage_map.keys())

            item_payloads = []
            for chemical_code in sorted(chemical_set):
                payload = build_item_result(
                    chemical_code=chemical_code,
                    lot=lot,
                    formula_version=formula_version,
                    formula_item=formula_items.get(chemical_code),
                    usage=usage_map.get(chemical_code),
                )
                item_payloads.append(payload)

            lot_status = derive_lot_status(item_payloads)
            lot_result = ReconciliationLotResult.objects.create(
                run=run,
                nf1=lot["nf1"],
                recurtimento_date=lot["data"],
                codpro=lot["codpro"],
                codder=lot["codder"],
                lot_weight=round_decimal(lot["peso"], 2),
                formula_version=formula_version,
                status_final=lot_status,
                has_inconsistency=lot_status == ReconciliationLotResult.STATUS_INCONSISTENT,
                has_divergence=lot_status == ReconciliationLotResult.STATUS_DIVERGENT,
                items_count=len(item_payloads),
            )

            for payload in item_payloads:
                ReconciliationItemResult.objects.create(
                    run=run,
                    lot_result=lot_result,
                    nf1=lot["nf1"],
                    **payload,
                )
                processed_items += 1

        if used_versions:
            FormulaVersion.objects.filter(id__in=used_versions).update(used_in_reconciliation=True)

        run.processed_lots = len(lots)
        run.processed_items = processed_items
        run.execution_time_ms = int((perf_counter() - started) * 1000)
        run.status = ReconciliationRun.STATUS_SUCCESS
        run.save(update_fields=["processed_lots", "processed_items", "execution_time_ms", "status", "updated_at"])
        return run
    except (OracleReconciliationError, ValueError) as exc:
        run.status = ReconciliationRun.STATUS_ERROR
        run.error_message = str(exc)
        run.execution_time_ms = int((perf_counter() - started) * 1000)
        run.save(update_fields=["status", "error_message", "execution_time_ms", "updated_at"])
        raise
