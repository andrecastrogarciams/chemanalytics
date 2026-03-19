from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_REVIEWER = "reviewer"
    ROLE_CONSULTA = "consulta"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_REVIEWER, "Reviewer"),
        (ROLE_CONSULTA, "Consulta"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CONSULTA)
    must_change_password = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role})"


class AdministrativeActionLog(models.Model):
    ACTION_CREATE_USER = "create_user"
    ACTION_DEACTIVATE_USER = "deactivate_user"
    ACTION_RESET_PASSWORD = "reset_password"
    ACTION_UPDATE_ROLE = "update_role"

    ACTION_CHOICES = [
        (ACTION_CREATE_USER, "Create user"),
        (ACTION_DEACTIVATE_USER, "Deactivate user"),
        (ACTION_RESET_PASSWORD, "Reset password"),
        (ACTION_UPDATE_ROLE, "Update role"),
    ]

    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="administrative_actions_received",
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="administrative_actions_performed",
    )
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
