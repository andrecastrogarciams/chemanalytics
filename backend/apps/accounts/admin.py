from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "must_change_password")
    list_filter = ("role", "must_change_password")
    search_fields = ("user__username",)
