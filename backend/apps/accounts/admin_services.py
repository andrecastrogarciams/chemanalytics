from django.contrib.auth.models import Group, User
from django.db import transaction

from .models import AdministrativeActionLog, UserProfile


def assign_role(user, role):
    existing_groups = Group.objects.filter(user=user, name__in=["admin", "reviewer", "consulta"])
    if existing_groups.exists():
        user.groups.remove(*existing_groups)
    group = Group.objects.get(name=role)
    user.groups.add(group)
    profile, _created = UserProfile.objects.get_or_create(user=user)
    profile.role = role
    profile.save(update_fields=["role"])
    return profile


@transaction.atomic
def create_admin_user(validated_data, performed_by):
    user = User.objects.create_user(
        username=validated_data["username"],
        password=validated_data["temporary_password"],
        first_name=validated_data.get("first_name", ""),
        last_name=validated_data.get("last_name", ""),
        is_active=True,
    )
    profile = assign_role(user, validated_data["role"])
    profile.must_change_password = True
    profile.save(update_fields=["must_change_password"])
    AdministrativeActionLog.objects.create(
        action=AdministrativeActionLog.ACTION_CREATE_USER,
        target_user=user,
        performed_by=performed_by,
        details={"role": validated_data["role"]},
    )
    return user


@transaction.atomic
def update_admin_user(user, validated_data, performed_by):
    updated_fields = []
    details = {}
    was_active = user.is_active

    for field in ("first_name", "last_name", "is_active"):
        if field in validated_data:
            old_value = getattr(user, field)
            new_value = validated_data[field]
            if old_value != new_value:
                setattr(user, field, new_value)
                updated_fields.append(field)
                details[field] = {"from": old_value, "to": new_value}

    if updated_fields:
        user.save(update_fields=updated_fields)

    if "role" in validated_data and user.profile.role != validated_data["role"]:
        previous_role = user.profile.role
        assign_role(user, validated_data["role"])
        AdministrativeActionLog.objects.create(
            action=AdministrativeActionLog.ACTION_UPDATE_ROLE,
            target_user=user,
            performed_by=performed_by,
            details={"from": previous_role, "to": validated_data["role"]},
        )

    if (
        "is_active" in validated_data
        and validated_data["is_active"] is False
        and was_active is True
    ):
        AdministrativeActionLog.objects.create(
            action=AdministrativeActionLog.ACTION_DEACTIVATE_USER,
            target_user=user,
            performed_by=performed_by,
            details={"reason": "manual_deactivation"},
        )

    return user


@transaction.atomic
def reset_user_password(user, temporary_password, performed_by):
    user.set_password(temporary_password)
    user.save(update_fields=["password"])
    profile, _created = UserProfile.objects.get_or_create(user=user)
    profile.must_change_password = True
    profile.save(update_fields=["must_change_password"])
    AdministrativeActionLog.objects.create(
        action=AdministrativeActionLog.ACTION_RESET_PASSWORD,
        target_user=user,
        performed_by=performed_by,
        details={"must_change_password": True},
    )
    return user
