import logging

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .admin_services import create_admin_user, reset_user_password, update_admin_user
from .models import AdministrativeActionLog, UserProfile
from .permissions import IsAdminRole, IsReviewerOrAdmin
from .serializers import (
    AdminUserCreateSerializer,
    AdminUserListSerializer,
    AdminUserResetPasswordSerializer,
    AdminUserUpdateSerializer,
    AdministrativeActionLogSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    RefreshSerializer,
    UserSerializer,
)


logger = logging.getLogger(__name__)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        try:
            is_valid = serializer.is_valid()
        except AuthenticationFailed:
            logger.warning("login_failed username=%s", request.data.get("username"))
            return Response(
                {"success": False, "code": "INVALID_CREDENTIALS", "message": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if is_valid:
            logger.info("login_success username=%s", request.data.get("username"))
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        logger.warning("login_failed username=%s", request.data.get("username"))
        detail = serializer.errors
        code_errors = detail.get("code", [])
        if code_errors and str(code_errors[0]) == "USER_INACTIVE":
            return Response(
                {"success": False, "code": "USER_INACTIVE", "message": "User is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(
            {"success": False, "code": "INVALID_CREDENTIALS", "errors": detail},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    def post(self, request):
        refresh = request.data.get("refresh")
        token = RefreshToken(refresh)
        token.blacklist()
        logger.info("logout username=%s", request.user.username)
        return Response({"success": True}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("password_changed username=%s", request.user.username)
        return Response({"success": True}, status=status.HTTP_200_OK)


class MeView(APIView):
    def get(self, request):
        profile, _created = UserProfile.objects.get_or_create(user=request.user)
        return Response({"success": True, "data": UserSerializer(request.user).data})


class ReviewerOnlyView(APIView):
    permission_classes = [IsReviewerOrAdmin]

    def get(self, request):
        return Response({"success": True, "message": "Authorized"})


class AdminUserCollectionView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        queryset = User.objects.select_related("profile").all().order_by("username")
        return Response({"success": True, "data": AdminUserListSerializer(queryset, many=True).data})

    def post(self, request):
        serializer = AdminUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = create_admin_user(serializer.validated_data, performed_by=request.user)
        logger.info("admin_user_created username=%s by=%s", user.username, request.user.username)
        return Response({"success": True, "data": AdminUserListSerializer(user).data}, status=status.HTTP_201_CREATED)


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminRole]

    def patch(self, request, user_id):
        user = get_object_or_404(User.objects.select_related("profile"), id=user_id)
        serializer = AdminUserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = update_admin_user(user, serializer.validated_data, performed_by=request.user)
        logger.info("admin_user_updated username=%s by=%s", updated.username, request.user.username)
        return Response({"success": True, "data": AdminUserListSerializer(updated).data})


class AdminUserResetPasswordView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, user_id):
        user = get_object_or_404(User.objects.select_related("profile"), id=user_id)
        serializer = AdminUserResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset_user_password(user, serializer.validated_data["temporary_password"], performed_by=request.user)
        logger.info("admin_user_password_reset username=%s by=%s", user.username, request.user.username)
        return Response({"success": True})


class AdminActionLogListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        queryset = AdministrativeActionLog.objects.select_related("target_user", "performed_by").all()
        return Response({"success": True, "data": AdministrativeActionLogSerializer(queryset, many=True).data})
