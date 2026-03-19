from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        profile = getattr(user, "profile", None)
        return bool(profile and profile.role in self.allowed_roles)


class IsReviewerOrAdmin(HasRole):
    allowed_roles = ("reviewer", "admin")


class IsAdminRole(HasRole):
    allowed_roles = ("admin",)


class IsAuthenticatedBusinessUser(HasRole):
    allowed_roles = ("admin", "reviewer", "consulta")
