from django.contrib import admin

from .models import Formula, FormulaItem, FormulaVersion


class FormulaItemInline(admin.TabularInline):
    model = FormulaItem
    extra = 0


class FormulaVersionInline(admin.TabularInline):
    model = FormulaVersion
    extra = 0


@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = ("codpro", "codder", "active", "updated_at")
    list_filter = ("active",)
    search_fields = ("codpro", "codder")
    inlines = [FormulaVersionInline]


@admin.register(FormulaVersion)
class FormulaVersionAdmin(admin.ModelAdmin):
    list_display = ("formula", "version_number", "start_date", "end_date", "active", "used_in_reconciliation")
    list_filter = ("active", "used_in_reconciliation")
    search_fields = ("formula__codpro", "formula__codder")
    inlines = [FormulaItemInline]


@admin.register(FormulaItem)
class FormulaItemAdmin(admin.ModelAdmin):
    list_display = ("formula_version", "chemical_code", "percentual", "tolerance_pct", "active")
    list_filter = ("active",)
    search_fields = ("chemical_code", "chemical_description")
