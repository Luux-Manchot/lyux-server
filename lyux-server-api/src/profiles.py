"""
Modèle de profils globaux LyuX (indépendants des bâtiments et salles).

Un profil est affecté globalement au niveau du lycée :
- socle global (tous les postes / tous les utilisateurs),
- paramètres établissement,
- rôle effectif de l'utilisateur,
- classe / groupe pédagogique,
- surcharge utilisateur,
- surcharge matériel explicite (poste spécifique).

Aucune distinction implicite de bâtiment ou de salle n'entre dans la résolution
du profil utilisateur, garantissant la mobilité dans tout le lycée.
"""

from typing import Any, Dict, List, Optional, Tuple

RESOLUTION_LAYERS: List[str] = [
    "global",
    "school",
    "role",
    "group",
    "user",
    "machine",
]

APPROVED_THEMES: List[Dict[str, str]] = [
    {"id": "lyux-ocean", "name": "LyuX Océan (Défaut)"},
    {"id": "lyux-dark", "name": "LyuX Sombre"},
    {"id": "lyux-light", "name": "LyuX Clair"},
]

APPROVED_THEME_IDS = {t["id"] for t in APPROVED_THEMES}

APPROVED_PACKAGES: List[str] = [
    "firefox-esr",
    "libreoffice",
    "vlc",
    "thonny",
    "code",
    "git",
    "python3-pytest",
    "geogebra",
    "veyon",
    "obs-studio",
    "stellarium",
    "avogadro",
    "gimp",
    "inkscape",
    "audacity",
    "kdenlive",
    "wireshark",
    "nmap",
    "htop",
    "arduino",
]

DEFAULT_PROFILES: Dict[str, Dict[str, Any]] = {
    "global-socle": {
        "id": "global-socle",
        "name": "Socle global lycée",
        "description": "Configuration commune appliquée à tous les utilisateurs et postes du lycée",
        "scope": "global",
        "kiosk_locked": False,
        "packages": ["firefox-esr", "libreoffice", "vlc"],
        "desktop_theme": "lyux-ocean",
    },
    "eleve": {
        "id": "eleve",
        "name": "Profil Élève",
        "description": "Environnement élève standard avec restrictions Kiosk",
        "scope": "role",
        "kiosk_locked": True,
        "packages": ["thonny", "geogebra"],
        "desktop_theme": "lyux-ocean",
    },
    "enseignant": {
        "id": "enseignant",
        "name": "Profil Professeur",
        "description": "Environnement pédagogique mobile avec Veyon Master et outils de classe",
        "scope": "role",
        "kiosk_locked": False,
        "packages": ["veyon", "libreoffice", "obs-studio"],
        "desktop_theme": "lyux-ocean",
    },
    "technicien": {
        "id": "technicien",
        "name": "Profil Technicien",
        "description": "Outils de diagnostic réseau, maintenance parc et console",
        "scope": "role",
        "kiosk_locked": False,
        "packages": ["wireshark", "nmap", "htop"],
        "desktop_theme": "lyux-dark",
    },
    "nsi": {
        "id": "nsi",
        "name": "Spécialité NSI",
        "description": "Environnement développement Python, C/C++, Web et Git",
        "scope": "group",
        "kiosk_locked": False,
        "packages": ["thonny", "code", "git", "python3-pytest"],
        "desktop_theme": "lyux-ocean",
    },
    "sciences": {
        "id": "sciences",
        "name": "Sciences & Labo",
        "description": "Outils de physique-chimie, SVT et acquisition",
        "scope": "group",
        "kiosk_locked": False,
        "packages": ["stellarium", "avogadro"],
        "desktop_theme": "lyux-ocean",
    },
    "multimedia": {
        "id": "multimedia",
        "name": "Arts & Multimédia",
        "description": "Création graphique, audio et montage vidéo",
        "scope": "group",
        "kiosk_locked": False,
        "packages": ["gimp", "inkscape", "audacity", "kdenlive"],
        "desktop_theme": "lyux-ocean",
    },
}

DEFAULT_PROFILE_ASSIGNMENTS: List[Dict[str, str]] = [
    {"target_type": "global", "target_id": "*", "profile_id": "global-socle"},
    {"target_type": "role", "target_id": "eleve", "profile_id": "eleve"},
    {"target_type": "role", "target_id": "enseignant", "profile_id": "enseignant"},
    {"target_type": "role", "target_id": "technicien", "profile_id": "technicien"},
    {"target_type": "group", "target_id": "T-NSI", "profile_id": "nsi"},
    {"target_type": "group", "target_id": "1-NSI", "profile_id": "nsi"},
]


def ensure_profiles_state(state: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, str]]]:
    profiles = state.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        profiles = {k: dict(v) for k, v in DEFAULT_PROFILES.items()}
    else:
        for pid, pdata in DEFAULT_PROFILES.items():
            profiles.setdefault(pid, dict(pdata))
    state["profiles"] = profiles

    assignments = state.get("profile_assignments")
    if not isinstance(assignments, list) or not assignments:
        assignments = [dict(a) for a in DEFAULT_PROFILE_ASSIGNMENTS]
    state["profile_assignments"] = assignments

    audit = state.get("profile_audit_log")
    if not isinstance(audit, list):
        state["profile_audit_log"] = []
    return profiles, assignments


def record_profile_audit(
    state: Dict[str, Any],
    actor: str,
    action: str,
    profile_id: str,
    detail: str,
) -> Dict[str, Any]:
    import datetime

    ensure_profiles_state(state)
    entry = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "actor": actor,
        "action": action,
        "profile_id": profile_id,
        "detail": detail,
    }
    state["profile_audit_log"].insert(0, entry)
    state["profile_audit_log"] = state["profile_audit_log"][:50]
    return entry


def resolve_effective_profile(
    state: Dict[str, Any],
    username: Optional[str] = None,
    role: Optional[str] = None,
    groups: Optional[List[str]] = None,
    hostname: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Résout le profil effectif en empilant les couches dans l'ordre :
    global -> school -> role -> group -> user -> machine.
    Les bâtiments et salles physiques sont volontairement ignorés.
    """
    profiles, assignments = ensure_profiles_state(state)
    school_setup = state.get("setup", {})
    school_default_profiles = school_setup.get("default_profiles") or []

    matched_ids: List[str] = []
    layers_trace: List[Dict[str, str]] = []

    def _add(layer: str, pid: str) -> None:
        if pid in profiles:
            if pid not in matched_ids:
                matched_ids.append(pid)
            layers_trace.append({"layer": layer, "profile_id": pid})

    # 1. Global
    for a in assignments:
        if a.get("target_type") == "global":
            _add("global", a["profile_id"])
    if not matched_ids and "global-socle" in profiles:
        _add("global", "global-socle")

    # 2. School
    for pid in school_default_profiles:
        if pid in profiles and pid == "standard":
            _add("school", pid)

    # 3. Role
    norm_role = (role or "").strip().lower()
    if norm_role:
        for a in assignments:
            if a.get("target_type") == "role" and a.get("target_id", "").lower() == norm_role:
                _add("role", a["profile_id"])

    # 4. Group / Classe
    norm_groups = {g.strip().upper() for g in (groups or []) if g and g.strip()}
    for a in assignments:
        if a.get("target_type") == "group" and a.get("target_id", "").upper() in norm_groups:
            _add("group", a["profile_id"])

    # 5. User
    norm_user = (username or "").strip().lower()
    if norm_user:
        for a in assignments:
            if a.get("target_type") == "user" and a.get("target_id", "").lower() == norm_user:
                _add("user", a["profile_id"])

    # 6. Machine (matériel spécifique uniquement, jamais de salle)
    norm_host = (hostname or "").strip().upper()
    if norm_host:
        for a in assignments:
            if a.get("target_type") == "machine" and a.get("target_id", "").upper() == norm_host:
                _add("machine", a["profile_id"])

    merged_packages: List[str] = []
    kiosk_locked = False
    desktop_theme = "lyux-ocean"
    primary_profile = matched_ids[-1] if matched_ids else "global-socle"

    for pid in matched_ids:
        prof = profiles[pid]
        for pkg in prof.get("packages", []):
            if pkg not in merged_packages:
                merged_packages.append(pkg)
        if "kiosk_locked" in prof:
            kiosk_locked = bool(prof["kiosk_locked"])
        if prof.get("desktop_theme"):
            desktop_theme = prof["desktop_theme"]

    return {
        "primary_profile": primary_profile,
        "applied_profiles": matched_ids,
        "layers": layers_trace,
        "packages": merged_packages,
        "kiosk_locked": kiosk_locked,
        "desktop_theme": desktop_theme,
        "location_independent": True,
    }
