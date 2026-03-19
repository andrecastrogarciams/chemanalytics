from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import UserProfile


DEFAULT_GROUPS = ("admin", "reviewer", "consulta")


@receiver(post_migrate)
def ensure_groups(sender, **kwargs):
    if sender.name != "apps.accounts":
        return

    for group_name in DEFAULT_GROUPS:
        Group.objects.get_or_create(name=group_name)


@receiver(post_save, sender="auth.User")
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
