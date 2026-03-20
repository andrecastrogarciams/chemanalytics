from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminRole

from .models import Formula, FormulaVersion
from .serializers import (
    FormulaCreateSerializer,
    FormulaSerializer,
    FormulaVersionCreateSerializer,
    FormulaVersionSerializer,
    FormulaVersionUpdateSerializer,
)


class FormulaListCreateView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        formulas = Formula.objects.select_related("article").prefetch_related("versions__items").all().order_by("codpro", "codder")
        return Response({"success": True, "data": FormulaSerializer(formulas, many=True).data})

    def post(self, request):
        serializer = FormulaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        formula = serializer.save()
        return Response(
            {"success": True, "data": FormulaSerializer(formula).data, "message": "created"},
            status=status.HTTP_201_CREATED,
        )


class FormulaDetailView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, formula_id):
        formula = get_object_or_404(Formula.objects.select_related("article").prefetch_related("versions__items"), pk=formula_id)
        return Response({"success": True, "data": FormulaSerializer(formula).data})


class FormulaVersionCreateView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, formula_id):
        formula = get_object_or_404(Formula, pk=formula_id)
        serializer = FormulaVersionCreateSerializer(data=request.data, context={"formula": formula})
        serializer.is_valid(raise_exception=True)
        version = serializer.save()
        return Response(
            {"success": True, "data": FormulaVersionSerializer(version).data, "message": "created"},
            status=status.HTTP_201_CREATED,
        )


class FormulaVersionUpdateView(APIView):
    permission_classes = [IsAdminRole]

    def patch(self, request, version_id):
        version = get_object_or_404(FormulaVersion.objects.prefetch_related("items"), pk=version_id)
        serializer = FormulaVersionUpdateSerializer(data=request.data, context={"version": version}, partial=True)
        serializer.is_valid(raise_exception=True)
        version = serializer.save()
        return Response({"success": True, "data": FormulaVersionSerializer(version).data})
