import base64
import datetime
import hashlib
import hmac
import json
import os
import socket
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from rbac import (
    DEFAULT_PERMISSION_MATRIX,
    DEFAULT_ROLES,
    RBAC_SCHEMA,
    RBAC_SCHEMA_VERSION,
    SYSTEM_ROLE_IDS,
    build_user_rbac_view,
    ensure_rbac_state,
    normalize_role_id,
    normalize_user_roles,
)
from profiles import (
    APPROVED_PACKAGES,
    APPROVED_THEMES,
    APPROVED_THEME_IDS,
    DEFAULT_PROFILES,
    RESOLUTION_LAYERS,
    ensure_profiles_state,
    record_profile_audit,
    resolve_effective_profile,
)
from sessions import check_and_register_session, register_logout, stable_uid_for_username

router = APIRouter(prefix="/api/v1", tags=["admin-ui"])

# Clé de signature des jetons HMAC (surchargeable via LYUX_AUTH_SECRET en production)
AUTH_SECRET = os.getenv("LYUX_AUTH_SECRET", "lyux-dev-secret-change-in-production").encode("utf-8")
TOKEN_TTL_SECONDS = int(os.getenv("LYUX_TOKEN_TTL", str(12 * 3600)))

# Persistance légère sur le volume /app/data (ou ./data en local)
DATA_DIR = Path(os.getenv("LYUX_DATA_DIR", "/app/data" if Path("/app/data").exists() else str(Path(__file__).resolve().parent.parent / "data")))
STATE_FILE = DATA_DIR / "admin_state.json"

DEFAULT_ROLES = [
    {"id": "admin", "name": "Administrateur", "description": "Accès complet au serveur et aux outils système"},
    {"id": "direction", "name": "Direction", "description": "Pilotage pédagogique et rapports consolidés"},
    {"id": "enseignant", "name": "Enseignant", "description": "Classes, partages pédagogiques et logiciels"},
    {"id": "viesco", "name": "Vie scolaire", "description": "Suivi des élèves et des inscriptions"},
    {"id": "eleve", "name": "Élève", "description": "Poste personnel et ressources de sa classe"},
]

DEFAULT_PERMISSION_MATRIX = [
    {"feature": "Tableau de bord", "admin": True, "direction": True, "enseignant": True, "viesco": True, "eleve": False},
    {"feature": "Parc & salles", "admin": True, "direction": False, "enseignant": False, "viesco": False, "eleve": False},
    {"feature": "Pilotage des mises à jour", "admin": True, "direction": False, "enseignant": False, "viesco": False, "eleve": False},
    {"feature": "Utilisateurs & classes", "admin": True, "direction": True, "enseignant": True, "viesco": True, "eleve": False},
    {"feature": "Logiciels", "admin": True, "direction": True, "enseignant": True, "viesco": False, "eleve": False},
    {"feature": "Versions OS & dépôt", "admin": True, "direction": False, "enseignant": False, "viesco": False, "eleve": False},
    {"feature": "Rôles & permissions", "admin": True, "direction": False, "enseignant": False, "viesco": False, "eleve": False},
    {"feature": "Intégrations", "admin": True, "direction": False, "enseignant": False, "viesco": False, "eleve": False},
    {"feature": "Configuration établissement", "admin": True, "direction": True, "enseignant": False, "viesco": False, "eleve": False},
]

DEFAULT_RELEASES = [
    {
        "id": "rel-1.0.0",
        "version": "1.0.0",
        "build": "20261122",
        "channel": "stable",
        "state": "published",
        "signature": "Vérifiée",
        "released_at": "2026-11-22",
        "size": "1.42 Go",
        "notes": "Version socle Debian 13 Trixie + KDE X11 + OOBE multi-établissements.",
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    },
    {
        "id": "rel-0.9.8",
        "version": "0.9.8",
        "build": "20261015",
        "channel": "archive",
        "state": "archived",
        "signature": "Vérifiée",
        "released_at": "2026-10-15",
        "size": "1.38 Go",
        "notes": "Ancienne image de test salle C14.",
        "sha256": "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
    },
]

DEFAULT_RELEASE_POLICY = {
    "channel": "stable",
    "auto_update": True,
    "update_window": "22:00 – 05:00",
    "require_signed": True,
    "canary_room": "C14",
}

DEFAULT_SETUP = {
    "configured": False,
    "school_name": "Lycée Opération Manchot",
    "uai_code": "",
    "academy": "",
    "school_year": "2026 – 2027",
    "domain": "lyux.lan",
    "admin_email": "administration@lyux.lan",
    "timezone": "Europe/Paris",
    "network": {
        "server_ip": "192.168.10.1",
        "subnet": "192.168.10.0/24",
        "gateway": "192.168.10.254",
        "dns": "192.168.10.1",
    },
    "modules": {
        "samba_ad": True,
        "glpi": True,
        "uptime_kuma": True,
        "apt_cache": True,
        "veyon": True,
        "sso": False,
    },
    "enrollment_enabled": True,
    "auto_update": True,
    "update_window": "22:00 – 05:00",
    "default_profiles": ["standard", "nsi", "sciences", "multimedia"],
    "updated_at": None,
}


def _load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "setup": dict(DEFAULT_SETUP),
        "roles": list(DEFAULT_ROLES),
        "permission_matrix": list(DEFAULT_PERMISSION_MATRIX),
        "releases": list(DEFAULT_RELEASES),
        "release_policy": dict(DEFAULT_RELEASE_POLICY),
    }


def _save_state(state: Dict[str, Any]) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # En test ou lecture seule, on garde l'état en mémoire sans bloquer
        pass


_STATE = _load_state()
ensure_rbac_state(_STATE)
ensure_profiles_state(_STATE)


def _get_registry():
    main_mod = _get_main_module()
    return main_mod.RELEASE_REGISTRY


def _find_user(username: str) -> Optional[Dict[str, Any]]:
    main_mod = _get_main_module()
    target = (username or "").strip().lower()
    for u in main_mod.TEST_USERS:
        if u.get("username", "").lower() == target:
            return u
    return None


def _require_auth(authorization: Optional[str]) -> Dict[str, Any]:
    token = _extract_bearer(authorization)
    payload = _verify_token(token) if token else None
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide ou expirée.",
        )
    roles_catalog, matrix = ensure_rbac_state(_STATE)
    user = _find_user(payload.get("sub", ""))
    if user is None:
        user = {
            "username": payload.get("sub", "unknown"),
            "display_name": payload.get("display_name", payload.get("sub", "unknown")),
            "roles": payload.get("roles") or [payload.get("role", "eleve")],
            "role": payload.get("role", "eleve"),
        }
    return build_user_rbac_view(user, roles_catalog, matrix)


def _require_permission(authorization: Optional[str], permission_key: str) -> Dict[str, Any]:
    user_view = _require_auth(authorization)
    if not user_view.get("permissions", {}).get(permission_key, False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission requise : {permission_key}",
        )
    return user_view


def _require_admin(authorization: Optional[str]) -> str:
    user_view = _require_auth(authorization)
    if user_view.get("effective_role") not in ("admin", "technicien"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentification administrateur ou technicien requise.",
        )
    return user_view["username"]


def _sign_token(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    b64 = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    sig = hmac.new(AUTH_SECRET, b64.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"


def _verify_token(token: str) -> Optional[Dict[str, Any]]:
    if not token or "." not in token:
        return None
    try:
        b64, sig = token.split(".", 1)
        expected = hmac.new(AUTH_SECRET, b64.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        padded = b64 + "=" * (-len(b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def _get_main_module():
    import main as main_mod
    return main_mod


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


class LoginRequest(BaseModel):
    username: str
    password: str


class SetupBuildingInput(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""


class SetupRoomInput(BaseModel):
    id: str
    building_id: str
    profile: str = "standard"
    capacity: int = 24
    teacher: Optional[str] = ""


class SetupPayload(BaseModel):
    school_name: str
    uai_code: Optional[str] = ""
    academy: Optional[str] = ""
    school_year: str = "2026 – 2027"
    domain: str = "lyux.lan"
    admin_email: str = "administration@lyux.lan"
    timezone: str = "Europe/Paris"
    network: Optional[Dict[str, str]] = None
    modules: Optional[Dict[str, bool]] = None
    enrollment_enabled: bool = True
    auto_update: bool = True
    update_window: str = "22:00 – 05:00"
    default_profiles: Optional[List[str]] = None
    buildings: Optional[List[SetupBuildingInput]] = None
    rooms: Optional[List[SetupRoomInput]] = None
    apply_topology: bool = False


class PermissionUpdatePayload(BaseModel):
    matrix: List[Dict[str, Any]]


class ReleaseCreatePayload(BaseModel):
    version: str
    profile_id: str = "standard"
    channel: str = "stable"
    family: str = "client"
    notes: str = ""
    size: str = "1.40 Go"
    artifacts: Optional[List[Dict[str, Any]]] = None


class ReleaseRevokePayload(BaseModel):
    reason: str = ""


class WakeRequest(BaseModel):
    hostname: str
    mac: Optional[str] = None


class RoleCreatePayload(BaseModel):
    id: Optional[str] = None
    name: str
    description: str = ""
    priority: int = 30
    permissions: Optional[Dict[str, bool]] = None


class UserUpdatePayload(BaseModel):
    display_name: Optional[str] = None
    role: Optional[str] = None
    roles: Optional[List[str]] = None
    classe: Optional[str] = None
    groups: Optional[List[str]] = None
    status: Optional[str] = None


# ------------------------------------------------------------------------------
# Authentification
# ------------------------------------------------------------------------------

@router.post("/auth/login")
def login(req: LoginRequest):
    main_mod = _get_main_module()
    username = req.username.strip().lower()
    matched = None
    for u in main_mod.TEST_USERS:
        if u.get("username", "").lower() == username and u.get("password") == req.password:
            matched = u
            break

    if not matched:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect.",
        )
    if matched.get("status") == "disabled":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé.",
        )

    roles_catalog, matrix = ensure_rbac_state(_STATE)
    user_view = build_user_rbac_view(matched, roles_catalog, matrix)

    now = int(time.time())
    token = _sign_token({
        "sub": matched["username"],
        "role": user_view["effective_role"],
        "roles": user_view["roles"],
        "display_name": user_view["display_name"],
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": TOKEN_TTL_SECONDS,
        "user": user_view,
    }


@router.get("/auth/me")
def auth_me(authorization: Optional[str] = Header(default=None)):
    user_view = _require_auth(authorization)
    roles_catalog, matrix = ensure_rbac_state(_STATE)
    return {
        **user_view,
        "rbac_schema": RBAC_SCHEMA,
        "rbac_schema_version": RBAC_SCHEMA_VERSION,
        "roles_catalog": roles_catalog,
        "permission_matrix": matrix,
    }


@router.post("/auth/logout")
def logout():
    return {"status": "ok"}


# ------------------------------------------------------------------------------
# Configuration / Onboarding Établissement (Lycée)
# ------------------------------------------------------------------------------

@router.get("/setup")
def get_setup():
    return _STATE.get("setup", DEFAULT_SETUP)


@router.post("/setup")
def save_setup(req: SetupPayload):
    main_mod = _get_main_module()
    setup_data = {
        "configured": True,
        "school_name": req.school_name.strip(),
        "uai_code": (req.uai_code or "").strip().upper(),
        "academy": (req.academy or "").strip(),
        "school_year": req.school_year.strip(),
        "domain": req.domain.strip() or "lyux.lan",
        "admin_email": req.admin_email.strip() or "administration@lyux.lan",
        "timezone": req.timezone.strip() or "Europe/Paris",
        "network": req.network or DEFAULT_SETUP["network"],
        "modules": req.modules or DEFAULT_SETUP["modules"],
        "enrollment_enabled": req.enrollment_enabled,
        "auto_update": req.auto_update,
        "update_window": req.update_window,
        "default_profiles": req.default_profiles or DEFAULT_SETUP["default_profiles"],
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    _STATE["setup"] = setup_data

    # Synchronise les réglages serveur actifs
    main_mod.SYSTEM_SETTINGS["enrollment_enabled"] = req.enrollment_enabled
    main_mod.SYSTEM_SETTINGS["auto_update_clients"] = req.auto_update
    if req.modules and "apt_cache" in req.modules:
        main_mod.SYSTEM_SETTINGS["apt_cache_enabled"] = req.modules["apt_cache"]

    created_buildings = 0
    created_rooms = 0
    if req.apply_topology:
        if req.buildings:
            for b in req.buildings:
                bid = b.id.strip().upper()
                if bid:
                    main_mod.BUILDINGS_CATALOG[bid] = {
                        "id": bid,
                        "name": b.name.strip() or bid,
                        "description": (b.description or "").strip(),
                    }
                    created_buildings += 1
        if req.rooms:
            for r in req.rooms:
                rid = r.id.strip().upper()
                if rid:
                    main_mod.ROOM_CATALOG[rid] = {
                        "id": rid,
                        "name": rid,
                        "building_id": r.building_id.strip().upper(),
                        "profile": r.profile,
                        "capacity": r.capacity,
                        "teacher": r.teacher or "",
                    }
                    created_rooms += 1

    _save_state(_STATE)
    return {
        "status": "configured",
        "setup": setup_data,
        "topology_applied": req.apply_topology,
        "created_buildings": created_buildings,
        "created_rooms": created_rooms,
    }


# ------------------------------------------------------------------------------
# Rôles & Permissions
# ------------------------------------------------------------------------------

@router.get("/roles")
def get_roles(authorization: Optional[str] = Header(default=None)):
    _require_permission(authorization, "roles.view")
    main_mod = _get_main_module()
    roles_catalog, matrix = ensure_rbac_state(_STATE)
    valid_ids = {r["id"] for r in roles_catalog}
    counts: Dict[str, int] = {r["id"]: 0 for r in roles_catalog}
    for u in main_mod.TEST_USERS:
        u_roles = normalize_user_roles(u.get("roles"), u.get("role"), valid_ids)
        for rid in u_roles:
            counts[rid] = counts.get(rid, 0) + 1

    roles_with_counts = []
    for r in roles_catalog:
        item = dict(r)
        item["members"] = counts.get(r["id"], 0)
        roles_with_counts.append(item)

    return {
        "schema": RBAC_SCHEMA,
        "schema_version": RBAC_SCHEMA_VERSION,
        "roles": roles_with_counts,
        "matrix": matrix,
    }


@router.post("/roles")
def create_role(req: RoleCreatePayload, authorization: Optional[str] = Header(default=None)):
    _require_permission(authorization, "roles.manage")
    roles_catalog, matrix = ensure_rbac_state(_STATE)
    raw_id = (req.id or req.name).strip().lower()
    role_id = "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in raw_id).strip("-_")
    role_id = normalize_role_id(role_id)
    if not role_id or any(r["id"] == role_id for r in roles_catalog):
        raise HTTPException(status_code=400, detail="Identifiant de rôle invalide ou déjà existant.")

    priority = max(1, min(int(req.priority), 99))
    new_role = {
        "id": role_id,
        "name": req.name.strip() or role_id,
        "description": req.description.strip(),
        "priority": priority,
        "system": False,
    }
    roles_catalog.append(new_role)
    perms = req.permissions or {}
    for row in matrix:
        key = row.get("key")
        row[role_id] = bool(perms.get(key, key == "dashboard.view"))
    ensure_rbac_state(_STATE)
    _save_state(_STATE)
    return {"status": "created", "role": new_role}


@router.delete("/roles/{role_id}")
def delete_role(role_id: str, authorization: Optional[str] = Header(default=None)):
    _require_permission(authorization, "roles.manage")
    rid = normalize_role_id(role_id)
    if rid in SYSTEM_ROLE_IDS:
        raise HTTPException(status_code=400, detail="Impossible de supprimer un rôle système par défaut.")
    roles_catalog, matrix = ensure_rbac_state(_STATE)
    if not any(r["id"] == rid for r in roles_catalog):
        raise HTTPException(status_code=404, detail="Rôle introuvable.")
    _STATE["roles"] = [r for r in roles_catalog if r["id"] != rid]
    for row in matrix:
        row.pop(rid, None)
    main_mod = _get_main_module()
    for u in main_mod.TEST_USERS:
        if "roles" in u and isinstance(u["roles"], list):
            u["roles"] = [r for r in u["roles"] if r != rid] or ["eleve"]
    ensure_rbac_state(_STATE)
    _save_state(_STATE)
    return {"status": "deleted", "role_id": rid}


@router.put("/roles/permissions")
def update_permissions(req: PermissionUpdatePayload, authorization: Optional[str] = Header(default=None)):
    _require_permission(authorization, "roles.manage")
    _STATE["permission_matrix"] = req.matrix
    _, matrix = ensure_rbac_state(_STATE)
    _save_state(_STATE)
    return {"status": "updated", "matrix": matrix}


# ------------------------------------------------------------------------------
# Versions OS & Dépôt (ADR-019)
# ------------------------------------------------------------------------------

@router.get("/releases")
def get_releases():
    main_mod = _get_main_module()
    reg_data = _get_registry().list_releases()
    return {
        "server_version": main_mod.SYSTEM_SETTINGS.get("lyux_version", "1.0.0"),
        "releases": reg_data["releases"],
        "policy": reg_data["policy"],
        "public_keys": reg_data["public_keys"],
        "audit_log": reg_data["audit_log"],
    }


@router.post("/releases")
def create_release(req: ReleaseCreatePayload, authorization: Optional[str] = Header(default=None)):
    actor = _require_admin(authorization) if authorization else "admin"
    ok, res = _get_registry().create_draft(
        version=req.version,
        profile_id=req.profile_id,
        channel=req.channel,
        family=req.family,
        notes=req.notes,
        artifacts=req.artifacts,
        actor=actor,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=res)
    return {"status": "created", "release": res}


@router.post("/releases/{release_id}/sign")
def sign_release_endpoint(release_id: str, authorization: Optional[str] = Header(default=None)):
    actor = _require_admin(authorization)
    ok, res = _get_registry().sign_release(release_id, actor=actor)
    if not ok:
        raise HTTPException(status_code=400, detail=res)
    return {"status": "signed", "release": res}


@router.post("/releases/{release_id}/publish")
def publish_release_endpoint(release_id: str, authorization: Optional[str] = Header(default=None)):
    actor = _require_admin(authorization)
    ok, res = _get_registry().publish_release(release_id, actor=actor)
    if not ok:
        raise HTTPException(status_code=400, detail=res)
    return {"status": "published", "release": res}


@router.post("/releases/{release_id}/revoke")
def revoke_release_endpoint(
    release_id: str,
    req: Optional[ReleaseRevokePayload] = None,
    authorization: Optional[str] = Header(default=None),
):
    actor = _require_admin(authorization)
    ok, res = _get_registry().revoke_release(release_id, actor=actor, reason=(req.reason if req else ""))
    if not ok:
        raise HTTPException(status_code=400, detail=res)
    return {"status": "revoked", "release": res}


@router.post("/releases/{release_id}/rollback")
def rollback_release_endpoint(release_id: str, authorization: Optional[str] = Header(default=None)):
    actor = _require_admin(authorization)
    ok, res = _get_registry().rollback_to_release(release_id, actor=actor)
    if not ok:
        raise HTTPException(status_code=400, detail=res)
    return {"status": "published", "release": res}


@router.post("/releases/keys/rotate")
def rotate_release_keys(authorization: Optional[str] = Header(default=None)):
    actor = _require_admin(authorization)
    reg = _get_registry()
    bundle = reg.key_manager.rotate_key()
    reg._record_audit(actor, "rotate_key", bundle["active_key_id"], f"Rotation Ed25519 (secours={bundle.get('backup_key_id')})")
    reg._atomic_save()
    return {"status": "rotated", "public_keys": bundle}


@router.get("/releases/audit")
def get_release_audit():
    return {"audit_log": _get_registry().list_releases()["audit_log"]}


@router.put("/releases/policy")
def update_release_policy(policy: Dict[str, Any]):
    updated = _get_registry().update_policy(policy)
    return {"status": "updated", "policy": updated}


# ------------------------------------------------------------------------------
# Intégrations & Résumé Dashboard & WOL
# ------------------------------------------------------------------------------

def _tcp_probe(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@router.get("/integrations/status")
def get_integrations_status():
    modules = _STATE.get("setup", DEFAULT_SETUP).get("modules", DEFAULT_SETUP["modules"])
    services = [
        {
            "id": "samba",
            "name": "Samba 4 Active Directory",
            "category": "Identité",
            "description": "Annuaire LDAP centralisé et partages CIFS des cours et devoirs.",
            "detail": "Ports 389 / 445 · socle système",
            "enabled": modules.get("samba_ad", True),
            "status": "active" if modules.get("samba_ad", True) else "disabled",
        },
        {
            "id": "kuma",
            "name": "Uptime Kuma",
            "category": "Supervision",
            "description": "Surveillance temps réel de l’infrastructure, sondes ICMP et alertes.",
            "detail": "Port 3001 · supervision.lyux.lan",
            "enabled": modules.get("uptime_kuma", True),
            "status": "active" if (_tcp_probe("supervision", 3001) or _tcp_probe("127.0.0.1", 3001) or modules.get("uptime_kuma", True)) else "offline",
        },
        {
            "id": "glpi",
            "name": "GLPI",
            "category": "Inventaire",
            "description": "Inventaire du parc, tickets d’incidents matériel et suivi des pannes.",
            "detail": "Port 8085 · glpi.lyux.lan",
            "enabled": modules.get("glpi", True),
            "status": "active" if (_tcp_probe("glpi", 80) or _tcp_probe("127.0.0.1", 8085) or modules.get("glpi", True)) else "offline",
        },
        {
            "id": "admin-ui",
            "name": "LyuX Admin UI",
            "category": "Interface",
            "description": "Interface unique d’administration du lycée, du parc, des profils et des rôles.",
            "detail": "Port 8087 · admin.lyux.lan",
            "enabled": True,
            "status": "active",
        },
        {
            "id": "hub",
            "name": "LyuX Hub (ancien panneau)",
            "category": "Interface",
            "description": "Ancien portail conteneurisé conservé en parallèle pendant la transition.",
            "detail": "Port 8086 · hub.lyux.lan",
            "enabled": True,
            "status": "active",
        },
        {
            "id": "proxy",
            "name": "Cache APT",
            "category": "Infrastructure",
            "description": "Mise en cache des paquets pour accélérer les mises à jour du parc client.",
            "detail": "Port 3142",
            "enabled": modules.get("apt_cache", True),
            "status": "active" if modules.get("apt_cache", True) else "disabled",
        },
        {
            "id": "sso",
            "name": "Authentification SSO",
            "category": "Identité",
            "description": "Connexion unique au panneau et aux services via l’annuaire.",
            "detail": "Configuré" if modules.get("sso", False) else "Non configuré",
            "enabled": modules.get("sso", False),
            "status": "active" if modules.get("sso", False) else "planned",
        },
    ]
    return {"services": services}


class MaintenancePasswordPayload(BaseModel):
    password: str


@router.post("/system/maintenance-password")
def set_maintenance_root_password(
    req: MaintenancePasswordPayload,
    authorization: Optional[str] = Header(default=None),
):
    import hashlib
    import os

    actor = _require_permission(authorization, "setup.manage")["username"]
    pwd = (req.password or "").strip()
    if len(pwd) < 8:
        raise HTTPException(status_code=400, detail="Le mot de passe root de maintenance doit contenir au moins 8 caractères.")
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt, 200_000)
    _STATE["maintenance_root"] = {
        "account": "root",
        "salt": base64.b64encode(salt).decode("ascii"),
        "hash": base64.b64encode(dk).decode("ascii"),
        "updated_by": actor,
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    _save_state(_STATE)
    return {
        "status": "updated",
        "account": "root",
        "maintenance_root_configured": True,
    }


class SessionLoginCheckPayload(BaseModel):
    username: str
    hostname: str
    ip: str = ""


class SessionLogoutPayload(BaseModel):
    username: str
    hostname: str
    files_synced: int = 0


class DesktopLoginPayload(BaseModel):
    username: str
    password: str
    hostname: str = ""
    ip: str = ""


@router.get("/client/nss-users")
def client_nss_users():
    """Catalogue NSS léger (sans mot de passe) pour synchroniser /var/lib/extrausers sur les postes."""
    main_mod = _get_main_module()
    roles_catalog, matrix = ensure_rbac_state(_STATE)
    users_out = []
    for u in main_mod.TEST_USERS:
        if u.get("status") == "disabled":
            continue
        uname = (u.get("username") or "").strip().lower()
        if not uname or uname in ("root", "lyux-admin", "invite"):
            continue
        view = build_user_rbac_view(u, roles_catalog, matrix)
        uid = stable_uid_for_username(uname)
        users_out.append({
            "username": uname,
            "uid": uid,
            "gid": uid,
            "display_name": view["display_name"],
            "effective_role": view["effective_role"],
            "home": f"/home/{uname}",
            "shell": "/bin/bash",
        })
    return {"users": users_out}


@router.post("/auth/desktop-login")
def desktop_login(req: DesktopLoginPayload):
    """Authentifie un utilisateur du lycée depuis SDDM/PAM sur un poste client."""
    uname = (req.username or "").strip().lower()
    user = _find_user(uname)
    if not user or user.get("status") == "disabled":
        raise HTTPException(status_code=401, detail="Utilisateur inconnu ou désactivé.")
    if user.get("password") != req.password:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect.")
    roles_catalog, matrix = ensure_rbac_state(_STATE)
    user_view = build_user_rbac_view(user, roles_catalog, matrix)
    allow_multi = bool(user_view.get("permissions", {}).get("sessions.multi", False))
    host = (req.hostname or "CLIENT").strip().upper()
    active_map = _STATE.get("active_sessions", {})
    other_hosts = [s for s in active_map.get(uname, []) if s.get("hostname") != host]
    if other_hosts and not allow_multi:
        raise HTTPException(
            status_code=409,
            detail=f"Utilisateur déjà connecté sur le poste {other_hosts[0]['hostname']}.",
        )
    return {
        "authenticated": True,
        "username": uname,
        "uid": stable_uid_for_username(uname),
        "effective_role": user_view["effective_role"],
        "roles": user_view["roles"],
    }


@router.post("/sessions/login-check")
def session_login_check(req: SessionLoginCheckPayload):
    user = _find_user(req.username)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur inconnu sur le serveur.")
    roles_catalog, matrix = ensure_rbac_state(_STATE)
    user_view = build_user_rbac_view(user, roles_catalog, matrix)
    allow_multi = bool(user_view.get("permissions", {}).get("sessions.multi", False))
    school_year = _STATE.get("setup", {}).get("school_year", "2026 – 2027")

    ok, code, payload = check_and_register_session(
        _STATE,
        username=user_view["username"],
        hostname=req.hostname,
        ip=req.ip,
        allow_multi_session=allow_multi,
        classe=user.get("classe"),
        school_year=school_year,
    )
    if not ok:
        raise HTTPException(status_code=code, detail=payload["detail"])
    _save_state(_STATE)
    return {**payload, "effective_role": user_view["effective_role"], "roles": user_view["roles"]}


@router.post("/sessions/logout")
def session_logout(req: SessionLogoutPayload):
    res = register_logout(
        _STATE,
        username=req.username,
        hostname=req.hostname,
        files_synced=req.files_synced,
    )
    _save_state(_STATE)
    return res


@router.get("/sessions/active")
def list_active_sessions(authorization: Optional[str] = Header(default=None)):
    _require_permission(authorization, "users.view")
    return {
        "active_sessions": _STATE.get("active_sessions", {}),
        "session_sync": _STATE.get("session_sync", {}),
    }


@router.get("/system/metrics")
def get_system_metrics():
    """Télémétrie système temps réel exposée directement pour l'Admin UI (port 8087)."""
    import os
    import platform
    import shutil

    disk = shutil.disk_usage("/")
    disk_total_gb = round(disk.total / (1024 ** 3), 1)
    disk_used_gb = round(disk.used / (1024 ** 3), 1)
    disk_pct = round((disk.used / disk.total) * 100, 1) if disk.total else 0.0

    cpu_count = os.cpu_count() or 1
    load_avg = None
    if hasattr(os, "getloadavg"):
        try:
            load_avg = round(os.getloadavg()[0], 2)
        except OSError:
            load_avg = None

    mem_total_gb = None
    mem_used_gb = None
    mem_pct = None
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        try:
            values = {}
            for line in meminfo.read_text(encoding="utf-8").splitlines():
                parts = line.split(":")
                if len(parts) == 2:
                    num = parts[1].strip().split()[0]
                    if num.isdigit():
                        values[parts[0]] = int(num)
            total_kb = values.get("MemTotal", 0)
            avail_kb = values.get("MemAvailable", values.get("MemFree", 0))
            if total_kb > 0:
                used_kb = max(0, total_kb - avail_kb)
                mem_total_gb = round(total_kb / (1024 ** 2), 1)
                mem_used_gb = round(used_kb / (1024 ** 2), 1)
                mem_pct = round((used_kb / total_kb) * 100, 1)
        except Exception:
            pass

    return {
        "platform": platform.system(),
        "hostname": platform.node(),
        "cpu_cores": cpu_count,
        "load_1m": load_avg,
        "memory": {
            "total_gb": mem_total_gb,
            "used_gb": mem_used_gb,
            "percent": mem_pct,
        },
        "disk": {
            "total_gb": disk_total_gb,
            "used_gb": disk_used_gb,
            "percent": disk_pct,
        },
    }


@router.get("/dashboard/summary")
def get_dashboard_summary():
    main_mod = _get_main_module()
    buildings = list(main_mod.BUILDINGS_CATALOG.values())
    rooms = list(main_mod.ROOM_CATALOG.values())
    machines = list(main_mod.INVENTORY_FLEET)
    apps = list(main_mod.APPS_CATALOG) if hasattr(main_mod, "APPS_CATALOG") else []
    users_count = len(main_mod.TEST_USERS)
    classes_count = len(main_mod.CLASSES_CATALOG)
    setup = _STATE.get("setup", DEFAULT_SETUP)

    return {
        "school_name": setup.get("school_name", "Lycée Opération Manchot"),
        "configured": setup.get("configured", False),
        "server_version": main_mod.SYSTEM_SETTINGS.get("lyux_version", "1.0.0"),
        "counts": {
            "buildings": len(buildings),
            "rooms": len(rooms),
            "machines": len(machines),
            "users": users_count,
            "classes": classes_count,
            "apps": len(apps),
        },
        "recent_tickets": getattr(main_mod, "RECENT_TICKETS", []),
    }


@router.post("/control/wake")
def wake_machine(req: WakeRequest):
    return {
        "status": "sent",
        "hostname": req.hostname,
        "mac": req.mac,
        "message": f"Paquet Wake-on-LAN envoyé vers {req.hostname}.",
    }


class ProfileUpsertPayload(BaseModel):
    id: str
    name: str
    description: str = ""
    scope: str = "group"
    kiosk_locked: bool = False
    packages: List[str] = []
    desktop_theme: str = "lyux-ocean"


class ProfileAssignPayload(BaseModel):
    target_type: str  # global | role | group | user | machine
    target_id: str
    profile_id: str


class ProfilePreviewPayload(BaseModel):
    profile_id: str
    desktop_theme: Optional[str] = None
    packages: Optional[List[str]] = None
    kiosk_locked: Optional[bool] = None
    target_type: str = "global"
    target_id: str = "*"


class ProfilePilotPayload(BaseModel):
    profile_id: str
    target_type: str = "machine"  # machine | group
    target_id: str


@router.get("/profiles")
def get_profiles(authorization: Optional[str] = Header(default=None)):
    _require_permission(authorization, "profiles.view")
    profiles, assignments = ensure_profiles_state(_STATE)
    return {
        "profiles": list(profiles.values()),
        "assignments": assignments,
        "resolution_layers": RESOLUTION_LAYERS,
        "approved_themes": APPROVED_THEMES,
        "approved_packages": APPROVED_PACKAGES,
        "audit_log": _STATE.get("profile_audit_log", []),
        "location_independent": True,
    }


@router.post("/profiles")
def upsert_profile(req: ProfileUpsertPayload, authorization: Optional[str] = Header(default=None)):
    actor = _require_permission(authorization, "profiles.manage")["username"]
    profiles, _ = ensure_profiles_state(_STATE)
    pid = req.id.strip().lower()
    if not pid:
        raise HTTPException(status_code=400, detail="Identifiant de profil requis.")
    if req.desktop_theme not in APPROVED_THEME_IDS:
        raise HTTPException(status_code=400, detail="Thème non approuvé dans le catalogue signé.")
    invalid_pkgs = [p for p in req.packages if p not in APPROVED_PACKAGES]
    if invalid_pkgs:
        raise HTTPException(status_code=400, detail=f"Paquets non approuvés : {', '.join(invalid_pkgs)}")

    profiles[pid] = {
        "id": pid,
        "name": req.name.strip() or pid,
        "description": req.description.strip(),
        "scope": req.scope,
        "kiosk_locked": req.kiosk_locked,
        "packages": list(dict.fromkeys(req.packages)),
        "desktop_theme": req.desktop_theme,
    }
    record_profile_audit(
        _STATE,
        actor,
        "save_profile",
        pid,
        f"Thème={req.desktop_theme}, {len(profiles[pid]['packages'])} paquet(s), kiosk={req.kiosk_locked}",
    )
    _save_state(_STATE)
    return {"status": "saved", "profile": profiles[pid]}


@router.post("/profiles/preview")
def preview_profile(req: ProfilePreviewPayload, authorization: Optional[str] = Header(default=None)):
    _require_permission(authorization, "profiles.view")
    main_mod = _get_main_module()
    profiles, _ = ensure_profiles_state(_STATE)
    base = profiles.get(req.profile_id, {})
    theme = req.desktop_theme or base.get("desktop_theme", "lyux-ocean")
    pkgs = req.packages if req.packages is not None else base.get("packages", [])
    kiosk = req.kiosk_locked if req.kiosk_locked is not None else base.get("kiosk_locked", False)

    if req.target_type == "global":
        affected_count = len(main_mod.INVENTORY_FLEET) + len(main_mod.TEST_USERS)
        scope_label = "Tout le lycée (tous postes et utilisateurs)"
    elif req.target_type == "role":
        affected_count = sum(1 for u in main_mod.TEST_USERS if req.target_id in (u.get("roles") or [u.get("role")]))
        scope_label = f"Rôle {req.target_id}"
    elif req.target_type == "group":
        affected_count = sum(1 for u in main_mod.TEST_USERS if (u.get("classe") or "").upper() == req.target_id.upper())
        scope_label = f"Classe / groupe {req.target_id}"
    elif req.target_type == "machine":
        affected_count = 1
        scope_label = f"Poste pilote {req.target_id}"
    else:
        affected_count = 1
        scope_label = f"Utilisateur {req.target_id}"

    return {
        "profile_id": req.profile_id,
        "scope_label": scope_label,
        "affected_count": affected_count,
        "desktop_theme": theme,
        "packages": pkgs,
        "kiosk_locked": kiosk,
        "pilot_recommended": req.target_type in ("global", "role"),
    }


@router.post("/profiles/pilot")
def pilot_profile(req: ProfilePilotPayload, authorization: Optional[str] = Header(default=None)):
    actor = _require_permission(authorization, "profiles.manage")["username"]
    if req.target_type not in ("machine", "group"):
        raise HTTPException(status_code=400, detail="Un pilote doit cibler un poste (machine) ou un groupe (group).")
    profiles, assignments = ensure_profiles_state(_STATE)
    if req.profile_id not in profiles:
        raise HTTPException(status_code=404, detail="Profil introuvable.")
    entry = {
        "target_type": req.target_type,
        "target_id": req.target_id.strip(),
        "profile_id": req.profile_id,
    }
    assignments = [
        a for a in assignments
        if not (a.get("target_type") == entry["target_type"] and a.get("target_id") == entry["target_id"])
    ]
    assignments.append(entry)
    _STATE["profile_assignments"] = assignments
    record_profile_audit(_STATE, actor, "pilot_apply", req.profile_id, f"Pilote sur {req.target_type}:{entry['target_id']}")
    _save_state(_STATE)
    return {"status": "pilot_applied", "assignment": entry}


@router.post("/profiles/{profile_id}/reset")
def reset_profile_to_default(profile_id: str, authorization: Optional[str] = Header(default=None)):
    actor = _require_permission(authorization, "profiles.manage")["username"]
    profiles, _ = ensure_profiles_state(_STATE)
    pid = profile_id.strip().lower()
    if pid not in DEFAULT_PROFILES:
        raise HTTPException(status_code=404, detail="Aucun profil par défaut LyuX correspondant.")
    profiles[pid] = dict(DEFAULT_PROFILES[pid])
    record_profile_audit(_STATE, actor, "reset_default", pid, "Restauration du profil LyuX par défaut")
    _save_state(_STATE)
    return {"status": "reset", "profile": profiles[pid]}


@router.post("/profiles/assign")
def assign_profile(req: ProfileAssignPayload, authorization: Optional[str] = Header(default=None)):
    actor = _require_permission(authorization, "profiles.manage")["username"]
    if req.target_type not in ("global", "role", "group", "user", "machine"):
        raise HTTPException(status_code=400, detail="target_type invalide (global, role, group, user, machine uniquement).")
    profiles, assignments = ensure_profiles_state(_STATE)
    if req.profile_id not in profiles:
        raise HTTPException(status_code=404, detail="Profil introuvable.")
    entry = {
        "target_type": req.target_type,
        "target_id": req.target_id.strip() or "*",
        "profile_id": req.profile_id,
    }
    assignments = [
        a for a in assignments
        if not (a.get("target_type") == entry["target_type"] and a.get("target_id") == entry["target_id"])
    ]
    assignments.append(entry)
    _STATE["profile_assignments"] = assignments
    record_profile_audit(_STATE, actor, "assign_profile", req.profile_id, f"Affecté à {req.target_type}:{entry['target_id']}")
    _save_state(_STATE)
    return {"status": "assigned", "assignment": entry}


@router.post("/profiles/unassign")
def unassign_profile(req: ProfileAssignPayload, authorization: Optional[str] = Header(default=None)):
    actor = _require_permission(authorization, "profiles.manage")["username"]
    _, assignments = ensure_profiles_state(_STATE)
    before = len(assignments)
    assignments = [
        a for a in assignments
        if not (
            a.get("target_type") == req.target_type
            and a.get("target_id") == req.target_id
            and a.get("profile_id") == req.profile_id
        )
    ]
    if len(assignments) == before:
        raise HTTPException(status_code=404, detail="Affectation introuvable.")
    _STATE["profile_assignments"] = assignments
    record_profile_audit(_STATE, actor, "unassign_profile", req.profile_id, f"Retiré de {req.target_type}:{req.target_id}")
    _save_state(_STATE)
    return {"status": "unassigned"}


@router.delete("/profiles/{profile_id}")
def delete_profile(profile_id: str, authorization: Optional[str] = Header(default=None)):
    actor = _require_permission(authorization, "profiles.manage")["username"]
    pid = profile_id.strip().lower()
    if pid in DEFAULT_PROFILES:
        raise HTTPException(status_code=400, detail="Impossible de supprimer un profil système par défaut.")
    profiles, assignments = ensure_profiles_state(_STATE)
    if pid not in profiles:
        raise HTTPException(status_code=404, detail="Profil introuvable.")
    profiles.pop(pid, None)
    _STATE["profile_assignments"] = [a for a in assignments if a.get("profile_id") != pid]
    record_profile_audit(_STATE, actor, "delete_profile", pid, "Profil personnalisé supprimé")
    _save_state(_STATE)
    return {"status": "deleted", "profile_id": pid}


@router.get("/profiles/resolve")
def resolve_profile_endpoint(
    username: Optional[str] = None,
    role: Optional[str] = None,
    groups: Optional[str] = None,
    hostname: Optional[str] = None,
):
    group_list = [g.strip() for g in groups.split(",")] if groups else []
    return resolve_effective_profile(
        _STATE,
        username=username,
        role=role,
        groups=group_list,
        hostname=hostname,
    )


@router.put("/users/{username}")
def update_user(
    username: str,
    req: UserUpdatePayload,
    authorization: Optional[str] = Header(default=None),
):
    _require_permission(authorization, "users.manage")
    main_mod = _get_main_module()
    roles_catalog, matrix = ensure_rbac_state(_STATE)
    valid_ids = {r["id"] for r in roles_catalog}
    target = username.strip().lower()
    for u in main_mod.TEST_USERS:
        if u.get("username", "").lower() == target:
            if req.display_name is not None:
                u["display_name"] = req.display_name.strip()
            if req.roles is not None:
                resolved_roles = normalize_user_roles(req.roles, None, valid_ids)
                u["roles"] = resolved_roles
                view = build_user_rbac_view(u, roles_catalog, matrix)
                u["role"] = view["effective_role"]
            elif req.role is not None:
                resolved_roles = normalize_user_roles([req.role], None, valid_ids)
                u["roles"] = resolved_roles
                view = build_user_rbac_view(u, roles_catalog, matrix)
                u["role"] = view["effective_role"]
            if req.classe is not None:
                u["classe"] = req.classe.strip()
            if req.groups is not None:
                u["groups"] = req.groups
            if req.status is not None:
                u["status"] = req.status
            main_mod.save_users_state()
            return {"status": "updated", "user": build_user_rbac_view(u, roles_catalog, matrix)}
    raise HTTPException(status_code=404, detail="Utilisateur introuvable.")


@router.delete("/users/{username}")
def delete_user(username: str, authorization: Optional[str] = Header(default=None)):
    actor = _require_permission(authorization, "users.manage")["username"]
    main_mod = _get_main_module()
    target = username.strip().lower()
    if target == actor.lower():
        raise HTTPException(status_code=400, detail="Impossible de supprimer votre propre compte actif.")
    idx = next((i for i, u in enumerate(main_mod.TEST_USERS) if u.get("username", "").lower() == target), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    user_obj = main_mod.TEST_USERS[idx]
    roles_catalog, matrix = ensure_rbac_state(_STATE)
    view = build_user_rbac_view(user_obj, roles_catalog, matrix)
    if view["effective_role"] == "admin":
        admin_count = sum(
            1 for u in main_mod.TEST_USERS
            if build_user_rbac_view(u, roles_catalog, matrix)["effective_role"] == "admin"
        )
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Impossible de supprimer le dernier administrateur.")
    main_mod.TEST_USERS.pop(idx)
    main_mod.save_users_state()
    return {"status": "deleted", "username": target}

