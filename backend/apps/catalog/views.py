from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsReviewerOrAdmin

from .models import ArticleCatalog, ChemicalProductCatalog, SyncJobRun
from .serializers import ArticleCatalogSerializer, ChemicalProductCatalogSerializer, SyncJobRunSerializer
from .services import sync_catalogs


class ArticleCatalogListView(APIView):
    permission_classes = [IsReviewerOrAdmin]

    def get(self, request):
        queryset = ArticleCatalog.objects.filter(active=True).order_by("codpro", "codder")
        return Response({"success": True, "data": ArticleCatalogSerializer(queryset, many=True).data})


class ChemicalCatalogListView(APIView):
    permission_classes = [IsReviewerOrAdmin]

    def get(self, request):
        queryset = ChemicalProductCatalog.objects.filter(active=True).order_by("chemical_code")
        return Response({"success": True, "data": ChemicalProductCatalogSerializer(queryset, many=True).data})


class SyncRunListView(APIView):
    permission_classes = [IsReviewerOrAdmin]

    def get(self, request):
        queryset = SyncJobRun.objects.all()
        return Response({"success": True, "data": SyncJobRunSerializer(queryset, many=True).data})


class SyncRunTriggerView(APIView):
    permission_classes = [IsReviewerOrAdmin]

    def post(self, request):
        sync_run = sync_catalogs(triggered_by=request.user)
        return Response(
            {"success": True, "data": {"sync_run_id": sync_run.id, "status": sync_run.status}},
            status=status.HTTP_202_ACCEPTED,
        )
