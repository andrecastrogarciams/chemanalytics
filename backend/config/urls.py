from django.contrib import admin
from django.urls import path

from apps.accounts.views import (
    AdminActionLogListView,
    AdminUserCollectionView,
    AdminUserDetailView,
    AdminUserResetPasswordView,
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    ReviewerOnlyView,
)
from apps.formulas.views import (
    FormulaDetailView,
    FormulaListCreateView,
    FormulaVersionCreateView,
    FormulaVersionUpdateView,
)
from apps.health.views import DependenciesHealthView, LiveHealthView
from apps.reconciliation.views import (
    ReconciliationItemReviewCreateView,
    ReconciliationLotDetailView,
    ReconciliationRunCollectionView,
    ReconciliationRunDetailView,
)
from apps.catalog.views import (
    ArticleCatalogListView,
    ChemicalCatalogListView,
    SyncRunListView,
    SyncRunTriggerView,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", LiveHealthView.as_view(), name="health-check"),
    path("api/v1/auth/login", LoginView.as_view(), name="auth-login"),
    path("api/v1/auth/refresh", RefreshView.as_view(), name="auth-refresh"),
    path("api/v1/auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("api/v1/auth/change-password", ChangePasswordView.as_view(), name="auth-change-password"),
    path("api/v1/auth/me", MeView.as_view(), name="auth-me"),
    path("api/v1/protected/reviewer", ReviewerOnlyView.as_view(), name="protected-reviewer"),
    path("api/v1/admin/users", AdminUserCollectionView.as_view(), name="admin-user-collection"),
    path("api/v1/admin/users/<int:user_id>", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("api/v1/admin/users/<int:user_id>/reset-password", AdminUserResetPasswordView.as_view(), name="admin-user-reset-password"),
    path("api/v1/admin/audit-log", AdminActionLogListView.as_view(), name="admin-audit-log"),
    path("api/v1/health/live", LiveHealthView.as_view(), name="health-live"),
    path("api/v1/health/dependencies", DependenciesHealthView.as_view(), name="health-dependencies"),
    path("api/v1/catalog/articles", ArticleCatalogListView.as_view(), name="catalog-articles"),
    path("api/v1/catalog/chemicals", ChemicalCatalogListView.as_view(), name="catalog-chemicals"),
    path("api/v1/sync/runs", SyncRunListView.as_view(), name="sync-run-list"),
    path("api/v1/sync/run", SyncRunTriggerView.as_view(), name="sync-run-trigger"),
    path("api/v1/formulas", FormulaListCreateView.as_view(), name="formula-list-create"),
    path("api/v1/formulas/<int:formula_id>", FormulaDetailView.as_view(), name="formula-detail"),
    path("api/v1/formulas/<int:formula_id>/versions", FormulaVersionCreateView.as_view(), name="formula-version-create"),
    path("api/v1/formula-versions/<int:version_id>", FormulaVersionUpdateView.as_view(), name="formula-version-update"),
    path("api/v1/reconciliation/runs", ReconciliationRunCollectionView.as_view(), name="reconciliation-run-collection"),
    path("api/v1/reconciliation/runs/<int:run_id>", ReconciliationRunDetailView.as_view(), name="reconciliation-run-detail"),
    path("api/v1/reconciliation/lots/<int:lot_id>", ReconciliationLotDetailView.as_view(), name="reconciliation-lot-detail"),
    path("api/v1/reconciliation/items/<int:item_id>/reviews", ReconciliationItemReviewCreateView.as_view(), name="reconciliation-item-review-create"),
]
