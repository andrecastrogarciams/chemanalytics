from django.db import transaction

from .models import ReconciliationItemResult, ReconciliationItemReview, ReconciliationLotResult


def derive_lot_flags_from_items(item_queryset):
    statuses = list(item_queryset.values_list("status_final", flat=True))
    if not statuses:
        return ReconciliationLotResult.STATUS_CONFORM, False, False

    has_inconsistency = ReconciliationItemResult.STATUS_INCONSISTENT in statuses
    has_divergence = ReconciliationItemResult.STATUS_DIVERGENT in statuses

    if has_inconsistency:
        lot_status = ReconciliationLotResult.STATUS_INCONSISTENT
    elif has_divergence:
        lot_status = ReconciliationLotResult.STATUS_DIVERGENT
    else:
        lot_status = ReconciliationLotResult.STATUS_CONFORM

    return lot_status, has_inconsistency, has_divergence


@transaction.atomic
def create_item_review(item_result, reviewed_status, justification, reviewed_by):
    previous_status = item_result.status_final
    review = ReconciliationItemReview.objects.create(
        item_result=item_result,
        previous_status=previous_status,
        reviewed_status=reviewed_status,
        justification=justification,
        reviewed_by=reviewed_by,
    )

    item_result.status_reviewed = reviewed_status
    item_result.status_final = reviewed_status
    item_result.save(update_fields=["status_reviewed", "status_final", "updated_at"])

    lot = item_result.lot_result
    lot_status, has_inconsistency, has_divergence = derive_lot_flags_from_items(lot.items.all())
    lot.status_final = lot_status
    lot.has_inconsistency = has_inconsistency
    lot.has_divergence = has_divergence
    lot.save(update_fields=["status_final", "has_inconsistency", "has_divergence", "updated_at"])

    return review
