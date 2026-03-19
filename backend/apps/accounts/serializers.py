from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

from .models import AdministrativeActionLog, UserProfile


class UserSerializer(serializers.ModelSerializer):
    group = serializers.CharField(source="profile.role")
    must_change_password = serializers.BooleanField(source="profile.must_change_password")

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "group", "must_change_password")


class LoginSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

    default_error_messages = {
        "no_active_account": "Invalid credentials.",
        "inactive_account": "USER_INACTIVE",
    }

    def validate(self, attrs):
        username = attrs.get("username")

        user = User.objects.filter(username=username).first()
        if user and not user.is_active:
            raise serializers.ValidationError({"code": "USER_INACTIVE", "message": "User is inactive."})

        data = super().validate(attrs)
        profile, _created = UserProfile.objects.get_or_create(user=self.user)

        return {
            "success": True,
            "data": {
                "access": data["access"],
                "refresh": data["refresh"],
                "user": UserSerializer(self.user).data,
            },
        }


class RefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        return {"success": True, "data": {"access": data["access"]}}


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        profile, _created = UserProfile.objects.get_or_create(user=user)
        profile.must_change_password = False
        profile.save(update_fields=["must_change_password"])
        return user


class AdminUserListSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role")
    must_change_password = serializers.BooleanField(source="profile.must_change_password")

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "is_active", "role", "must_change_password")


class AdminUserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES)
    temporary_password = serializers.CharField(min_length=8)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("username already exists.")
        return value


class AdminUserUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("At least one field must be provided.")
        return attrs


class AdminUserResetPasswordSerializer(serializers.Serializer):
    temporary_password = serializers.CharField(min_length=8)


class AdministrativeActionLogSerializer(serializers.ModelSerializer):
    target_username = serializers.CharField(source="target_user.username", read_only=True)
    performed_by_username = serializers.CharField(source="performed_by.username", read_only=True)

    class Meta:
        model = AdministrativeActionLog
        fields = ("id", "action", "target_username", "performed_by_username", "details", "created_at")
