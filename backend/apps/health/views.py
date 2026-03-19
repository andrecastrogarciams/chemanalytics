import logging

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole

from .services import build_dependencies_payload, build_live_payload


logger = logging.getLogger(__name__)


class LiveHealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        payload = build_live_payload()
        logger.info("health_live status=%s", payload["status"])
        return Response(payload)


class DependenciesHealthView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        payload = build_dependencies_payload()
        logger.info("health_dependencies status=%s", payload["status"])
        return Response(payload)
