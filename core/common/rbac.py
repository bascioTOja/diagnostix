from __future__ import annotations

from dataclasses import dataclass

from users.models import RoleChoices

ROLE_ADMINISTRATOR = RoleChoices.ADMINISTRATOR
ROLE_DIAGNOSTA = RoleChoices.DIAGNOSTA
ROLE_KLIENT = RoleChoices.KLIENT


@dataclass(frozen=True)
class AccessRule:
    action: str
    allowed_roles: tuple[str, ...]
    scope: str


RBAC_RULES: dict[str, AccessRule] = {
    "users.manage": AccessRule(
        action="users.manage",
        allowed_roles=(ROLE_ADMINISTRATOR,),
        scope="global",
    ),
    "stations.manage": AccessRule(
        action="stations.manage",
        allowed_roles=(ROLE_ADMINISTRATOR,),
        scope="global",
    ),
    "vehicles.client_crud": AccessRule(
        action="vehicles.client_crud",
        allowed_roles=(ROLE_KLIENT,),
        scope="own_only",
    ),
    "vehicles.admin_read": AccessRule(
        action="vehicles.admin_read",
        allowed_roles=(ROLE_ADMINISTRATOR,),
        scope="global_read",
    ),
    "appointments.book": AccessRule(
        action="appointments.book",
        allowed_roles=(ROLE_KLIENT,),
        scope="own_only",
    ),
    "inspections.result_add": AccessRule(
        action="inspections.result_add",
        allowed_roles=(ROLE_DIAGNOSTA,),
        scope="assigned_only",
    ),
    "inspections.history_view": AccessRule(
        action="inspections.history_view",
        allowed_roles=(ROLE_ADMINISTRATOR, ROLE_DIAGNOSTA, ROLE_KLIENT),
        scope="global_or_assigned_or_own",
    ),
    "analytics.view": AccessRule(
        action="analytics.view",
        allowed_roles=(ROLE_ADMINISTRATOR,),
        scope="global",
    ),
    "admin.panel": AccessRule(
        action="admin.panel",
        allowed_roles=(ROLE_ADMINISTRATOR,),
        scope="global",
    ),
}


def get_user_role(user) -> str | None:
    if not getattr(user, "is_authenticated", False):
        return None
    return getattr(user, "role", None)


def user_has_any_role(user, roles: tuple[str, ...] | list[str] | set[str]) -> bool:
    user_role = get_user_role(user)
    return bool(user_role and user_role in set(roles))


def action_allowed(user, action: str) -> bool:
    rule = RBAC_RULES.get(action)
    if not rule:
        return False
    return user_has_any_role(user, rule.allowed_roles)


def is_owner(user, obj, owner_attr: str = "owner_id") -> bool:
    user_id = getattr(user, "id", None)
    return bool(user_id and getattr(obj, owner_attr, None) == user_id)


def is_assigned_diagnosta(user, obj, diagnosta_attr: str = "diagnosta_id") -> bool:
    user_id = getattr(user, "id", None)
    return bool(user_id and getattr(obj, diagnosta_attr, None) == user_id)

