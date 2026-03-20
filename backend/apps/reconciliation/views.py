from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAuthenticatedBusinessUser, IsReviewerOrAdmin

from .models import ReconciliationItemResult, ReconciliationLotResult, ReconciliationRun
from .oracle_adapter import OracleReconciliationError
from .review_services import create_item_review
from .serializers import (
    ReconciliationLotDetailSerializer,
    ReconciliationItemReviewCreateSerializer,
    ReconciliationItemWithReviewsSerializer,
    ReconciliationRunDetailSerializer,
    ReconciliationRunListQuerySerializer,
    ReconciliationRunListSerializer,
    ReconciliationRunRequestSerializer,
    ReconciliationRunResponseSerializer,
)
from .services import execute_reconciliation


class ReconciliationRunCollectionView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsReviewerOrAdmin()]
        return [IsAuthenticatedBusinessUser()]

    def get(self, request):
        filters = ReconciliationRunListQuerySerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)

        queryset = ReconciliationRun.objects.select_related("executed_by").all()
        validated = filters.validated_data

        if validated.get("status"):
            queryset = queryset.filter(status=validated["status"])
        if validated.get("date_start"):
            queryset = queryset.filter(executed_at__date__gte=validated["date_start"])
        if validated.get("date_end"):
            queryset = queryset.filter(executed_at__date__lte=validated["date_end"])
        if validated.get("executed_by"):
            queryset = queryset.filter(executed_by__username__icontains=validated["executed_by"])

        return Response({"success": True, "data": ReconciliationRunListSerializer(queryset, many=True).data})

    def post(self, request):
        serializer = ReconciliationRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            run = execute_reconciliation(serializer.validated_data, executed_by=request.user)
        except OracleReconciliationError:
            return Response(
                {"success": False, "error": {"code": "ORACLE_UNAVAILABLE", "message": "Oracle is unavailable."}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {"success": True, "data": ReconciliationRunResponseSerializer(run).data},
            status=status.HTTP_201_CREATED,
        )


class ReconciliationRunDetailView(APIView):
    permission_classes = [IsAuthenticatedBusinessUser]

    def get(self, request, run_id):
        run = get_object_or_404(
            ReconciliationRun.objects.select_related("executed_by").prefetch_related(
                Prefetch(
                    "lots",
                    queryset=ReconciliationLotResult.objects.select_related("formula_version__formula__article"),
                )
            ),
            id=run_id,
        )
        return Response({"success": True, "data": ReconciliationRunDetailSerializer(run).data})


class ReconciliationLotDetailView(APIView):
    permission_classes = [IsAuthenticatedBusinessUser]

    def get(self, request, lot_id):
        lot = get_object_or_404(
            ReconciliationLotResult.objects.select_related("formula_version__formula__article").prefetch_related(
                "items__formula_version",
                "items__reviews__reviewed_by",
            ),
            id=lot_id,
        )
        return Response({"success": True, "data": ReconciliationLotDetailSerializer(lot).data})


class ReconciliationItemReviewCreateView(APIView):
    permission_classes = [IsReviewerOrAdmin]

    def post(self, request, item_id):
        item = get_object_or_404(
            ReconciliationItemResult.objects.select_related("lot_result", "formula_version").prefetch_related("reviews__reviewed_by"),
            id=item_id,
        )
        serializer = ReconciliationItemReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        create_item_review(
            item_result=item,
            reviewed_status=serializer.validated_data["reviewed_status"],
            justification=serializer.validated_data["justification"],
            reviewed_by=request.user,
        )
        item.refresh_from_db()
        return Response(
            {"success": True, "data": ReconciliationItemWithReviewsSerializer(item).data},
            status=status.HTTP_201_CREATED,
        )
