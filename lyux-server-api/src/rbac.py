"""
Module RBAC (Role-Based Access Control) pour LyuX Server API.

Gère :
- Les 6 rôles système par défaut (admin, technicien, direction, viesco, enseignant, eleve)
  avec niveaux de priorité explicites ;
- La création/modification/suppression de rôles personnalisés ;
- La matrice de permissions versionnée (schema_version = 1) ;
- La résolution multi-rôles : rôle effectif = rôle de priorité maximale,
  permissions effectives = union des permissions des rôles attribués.
"""

from typing import Any, Dict, List, Optional, Tuple

RBAC_SCHEMA = "lyux-rbac-matrix"
RBAC_SCHEMA_VERSION = 1

ROLE_ALIASES: Dict[str, str] = {
    "prof": "enseignant",
    "professeur": "enseignant",
    "teacher": "enseignant",
    "vie_scolaire": "viesco",
    "vie-scolaire": "viesco",
    "student": "eleve",
    "élèves": "eleve",
    "eleves": "eleve",
    "tech": "technicien",
    "administrator": "admin",
}

DEFAULT_ROLES: List[Dict[str, Any]] = [
    {
        "id": "admin",
        "name": "Administrateur",
        "description": "Accès complet au serveur, aux comptes, aux profils et aux outils système",
        "priority": 100,
        "system": True,
    },
    {
        "id": "technicien",
        "name": "Technicien",
        "description": "Maintenance du parc, postes, dépôts, profils globaux et diagnostic technique",
        "priority": 85,
        "system": True,
    },
    {
        "id": "direction",
        "name": "Direction",
        "description": "Pilotage de l'établissement, rapports consolidés et consultation du parc",
        "priority": 70,
        "system": True,
    },
    {
        "id": "viesco",
        "name": "Vie scolaire",
        "description": "Suivi des élèves, classes, inscriptions et réinitialisation de mots de passe",
        "priority": 55,
        "system": True,
    },
    {
        "id": "enseignant",
        "name": "Professeur",
        "description": "Classes, ressources pédagogiques, catalogue logiciel et verrouillage de séance",
        "priority": 40,
        "system": True,
    },
    {
        "id": "eleve",
        "name": "Élève",
        "description": "Poste personnel, profil élève et ressources de sa classe",
        "priority": 10,
        "system": True,
    },
]

SYSTEM_ROLE_IDS = {r["id"] for r in DEFAULT_ROLES}

DEFAULT_PERMISSION_MATRIX: List[Dict[str, Any]] = [
    {
        "key": "dashboard.view",
        "feature": "Tableau de bord & indicateurs",
        "admin": True,
        "technicien": True,
        "direction": True,
        "viesco": True,
        "enseignant": True,
        "eleve": True,
    },
    {
        "key": "parc.view",
        "feature": "Consulter le parc, bâtiments et salles",
        "admin": True,
        "technicien": True,
        "direction": True,
        "viesco": True,
        "enseignant": True,
        "eleve": False,
    },
    {
        "key": "parc.manage",
        "feature": "Gérer bâtiments, salles, postes et Wake-on-LAN",
        "admin": True,
        "technicien": True,
        "direction": False,
        "viesco": False,
        "enseignant": False,
        "eleve": False,
    },
    {
        "key": "parc.room_lock",
        "feature": "Verrouiller / piloter une séance en salle",
        "admin": True,
        "technicien": True,
        "direction": False,
        "viesco": True,
        "enseignant": True,
        "eleve": False,
    },
    {
        "key": "apps.view",
        "feature": "Consulter le catalogue d'applications",
        "admin": True,
        "technicien": True,
        "direction": True,
        "viesco": True,
        "enseignant": True,
        "eleve": True,
    },
    {
        "key": "apps.manage",
        "feature": "Ajouter et déployer des applications",
        "admin": True,
        "technicien": True,
        "direction": False,
        "viesco": False,
        "enseignant": False,
        "eleve": False,
    },
    {
        "key": "profiles.view",
        "feature": "Consulter les profils globaux lycée",
        "admin": True,
        "technicien": True,
        "direction": True,
        "viesco": True,
        "enseignant": True,
        "eleve": False,
    },
    {
        "key": "profiles.manage",
        "feature": "Configurer et affecter les profils globaux",
        "admin": True,
        "technicien": True,
        "direction": False,
        "viesco": False,
        "enseignant": False,
        "eleve": False,
    },
    {
        "key": "releases.view",
        "feature": "Consulter les versions OS et le dépôt APT",
        "admin": True,
        "technicien": True,
        "direction": True,
        "viesco": False,
        "enseignant": False,
        "eleve": False,
    },
    {
        "key": "releases.manage",
        "feature": "Signer, publier et révoquer des releases OS",
        "admin": True,
        "technicien": True,
        "direction": False,
        "viesco": False,
        "enseignant": False,
        "eleve": False,
    },
    {
        "key": "users.view",
        "feature": "Consulter les comptes et classes",
        "admin": True,
        "technicien": True,
        "direction": True,
        "viesco": True,
        "enseignant": True,
        "eleve": False,
    },
    {
        "key": "users.manage",
        "feature": "Créer/modifier comptes, classes et mots de passe",
        "admin": True,
        "technicien": False,
        "direction": False,
        "viesco": True,
        "enseignant": False,
        "eleve": False,
    },
    {
        "key": "roles.view",
        "feature": "Consulter les rôles et la matrice de permissions",
        "admin": True,
        "technicien": True,
        "direction": True,
        "viesco": False,
        "enseignant": False,
        "eleve": False,
    },
    {
        "key": "roles.manage",
        "feature": "Créer des rôles et modifier les permissions",
        "admin": True,
        "technicien": False,
        "direction": False,
        "viesco": False,
        "enseignant": False,
        "eleve": False,
    },
    {
        "key": "setup.manage",
        "feature": "Configurer l'établissement, les modules et le serveur",
        "admin": True,
        "technicien": True,
        "direction": False,
        "viesco": False,
        "enseignant": False,
        "eleve": False,
    },
    {
        "key": "cockpit.access",
        "feature": "Accéder à la console système native (Cockpit)",
        "admin": True,
        "technicien": True,
        "direction": False,
        "viesco": False,
        "enseignant": False,
        "eleve": False,
    },
    {
        "key": "sessions.multi",
        "feature": "Autoriser les sessions simultanées sur plusieurs postes",
        "admin": True,
        "technicien": True,
        "direction": True,
        "viesco": False,
        "enseignant": True,
        "eleve": False,
    },
]


def normalize_role_id(role_id: Optional[str]) -> str:
    raw = (role_id or "eleve").strip().lower()
    return ROLE_ALIASES.get(raw, raw)


def normalize_user_roles(
    roles: Optional[List[str]] = None,
    fallback_role: Optional[str] = None,
    valid_role_ids: Optional[set] = None,
) -> List[str]:
    candidates: List[str] = []
    if roles:
        for r in roles:
            nr = normalize_role_id(r)
            if nr and nr not in candidates:
                candidates.append(nr)
    if not candidates and fallback_role:
        nr = normalize_role_id(fallback_role)
        if nr:
            candidates.append(nr)
    if valid_role_ids is not None:
        candidates = [r for r in candidates if r in valid_role_ids]
    if not candidates:
        candidates = ["eleve"]
    return candidates


def ensure_rbac_state(state: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Garantit la présence des 6 rôles système et de toutes les clés de permission."""
    existing_roles = state.get("roles")
    if not isinstance(existing_roles, list) or not existing_roles:
        roles = [dict(r) for r in DEFAULT_ROLES]
    else:
        by_id = {r["id"]: dict(r) for r in existing_roles if isinstance(r, dict) and r.get("id")}
        roles = []
        for default_r in DEFAULT_ROLES:
            rid = default_r["id"]
            if rid in by_id:
                merged = {**default_r, **by_id[rid], "system": True}
                if "priority" not in by_id[rid]:
                    merged["priority"] = default_r["priority"]
                roles.append(merged)
            else:
                roles.append(dict(default_r))
        for rid, r in by_id.items():
            if rid not in SYSTEM_ROLE_IDS:
                r.setdefault("priority", 20)
                r["system"] = False
                roles.append(r)

    roles.sort(key=lambda r: (-int(r.get("priority", 0)), r["id"]))
    state["roles"] = roles

    existing_matrix = state.get("permission_matrix")
    if not isinstance(existing_matrix, list) or not existing_matrix:
        matrix = [dict(row) for row in DEFAULT_PERMISSION_MATRIX]
    else:
        by_key = {
            row.get("key"): dict(row)
            for row in existing_matrix
            if isinstance(row, dict) and row.get("key")
        }
        matrix = []
        for default_row in DEFAULT_PERMISSION_MATRIX:
            key = default_row["key"]
            merged_row = dict(default_row)
            if key in by_key:
                for role_obj in roles:
                    rid = role_obj["id"]
                    if rid in by_key[key]:
                        merged_row[rid] = bool(by_key[key][rid])
            for role_obj in roles:
                rid = role_obj["id"]
                merged_row.setdefault(rid, rid == "admin")
            matrix.append(merged_row)
    state["permission_matrix"] = matrix
    state["rbac_schema"] = RBAC_SCHEMA
    state["rbac_schema_version"] = RBAC_SCHEMA_VERSION
    return roles, matrix


def resolve_effective_role(user_roles: List[str], roles_catalog: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Retourne l'objet rôle ayant la priorité la plus élevée parmi `user_roles`."""
    catalog_by_id = {r["id"]: r for r in roles_catalog}
    matched = [catalog_by_id[r] for r in user_roles if r in catalog_by_id]
    if not matched:
        return catalog_by_id.get("eleve", DEFAULT_ROLES[-1])
    matched.sort(key=lambda r: (-int(r.get("priority", 0)), r["id"]))
    return matched[0]


def resolve_user_permissions(
    user_roles: List[str],
    roles_catalog: List[Dict[str, Any]],
    matrix: List[Dict[str, Any]],
) -> Dict[str, bool]:
    """Calcule les permissions effectives (union des rôles attribués ; admin a tout)."""
    if "admin" in user_roles:
        return {row["key"]: True for row in matrix if row.get("key")}
    perms: Dict[str, bool] = {}
    for row in matrix:
        key = row.get("key")
        if not key:
            continue
        perms[key] = any(bool(row.get(rid, False)) for rid in user_roles)
    return perms


def build_user_rbac_view(
    user: Dict[str, Any],
    roles_catalog: List[Dict[str, Any]],
    matrix: List[Dict[str, Any]],
) -> Dict[str, Any]:
    valid_ids = {r["id"] for r in roles_catalog}
    roles = normalize_user_roles(user.get("roles"), user.get("role"), valid_ids)
    effective = resolve_effective_role(roles, roles_catalog)
    permissions = resolve_user_permissions(roles, roles_catalog, matrix)
    return {
        "username": user.get("username"),
        "display_name": user.get("display_name") or user.get("username"),
        "role": effective["id"],
        "effective_role": effective["id"],
        "effective_role_name": effective.get("name", effective["id"]),
        "effective_priority": int(effective.get("priority", 0)),
        "roles": roles,
        "permissions": permissions,
        "classe": user.get("classe", "—"),
        "groups": user.get("groups", []),
        "status": user.get("status", "active"),
    }
