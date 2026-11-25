"""
Gestion des sessions actives, du verrouillage multi-session selon le rôle RBAC
et de l'emplacement permanent du home NAS (/srv/samba/homes/<uid>).
"""

import datetime
from typing import Any, Dict, List, Optional, Tuple

NAS_BASE = "/srv/samba"


def get_nas_paths(username: str, classe: Optional[str], school_year: str = "2026-2027") -> Dict[str, str]:
    uid = (username or "").strip().lower()
    clean_year = (school_year or "2026-2027").replace(" ", "").replace("–", "-")
    paths = {
        "home_path": f"{NAS_BASE}/homes/{uid}",
        "common_path": f"{NAS_BASE}/commun",
        "archive_base": f"{NAS_BASE}/archives",
    }
    if classe and classe not in ("—", "-", "Sans affectation", "Toutes"):
        paths["class_path"] = f"{NAS_BASE}/classes/{clean_year}/{classe.strip().upper()}"
    return paths


def check_and_register_session(
    state: Dict[str, Any],
    *,
    username: str,
    hostname: str,
    ip: str = "",
    allow_multi_session: bool = False,
    classe: Optional[str] = None,
    school_year: str = "2026-2027",
) -> Tuple[bool, int, Dict[str, Any]]:
    uname = (username or "").strip().lower()
    host = (hostname or "").strip().upper()
    if not uname or not host:
        return False, 400, {"detail": "Nom d'utilisateur et nom de poste requis."}

    active_map: Dict[str, List[Dict[str, Any]]] = state.setdefault("active_sessions", {})
    sync_map: Dict[str, Dict[str, Any]] = state.setdefault("session_sync", {})

    current_sessions = active_map.get(uname, [])
    other_hosts = [s for s in current_sessions if s.get("hostname") != host]

    if other_hosts and not allow_multi_session:
        other = other_hosts[0]["hostname"]
        return (
            False,
            409,
            {
                "detail": f"Utilisateur déjà connecté sur le poste {other}.",
                "code": "ALREADY_LOGGED_IN",
                "active_hostname": other,
                "multi_session_allowed": False,
            },
        )

    now = datetime.datetime.now().isoformat(timespec="seconds")
    updated_sessions = [s for s in current_sessions if s.get("hostname") != host]
    updated_sessions.append({
        "hostname": host,
        "ip": ip,
        "started_at": now,
        "last_seen": now,
    })
    active_map[uname] = updated_sessions

    prev_sync = sync_map.get(uname, {})
    last_machine = prev_sync.get("last_machine")
    needs_delta_sync = bool(last_machine and last_machine != host) or not prev_sync.get("last_sync_at")

    nas_paths = get_nas_paths(uname, classe, school_year=school_year)
    return (
        True,
        200,
        {
            "allowed": True,
            "username": uname,
            "hostname": host,
            "multi_session_allowed": allow_multi_session,
            "active_sessions": updated_sessions,
            "last_machine": last_machine,
            "last_sync_at": prev_sync.get("last_sync_at"),
            "needs_delta_sync": needs_delta_sync,
            "nas": nas_paths,
        },
    )


def register_logout(
    state: Dict[str, Any],
    *,
    username: str,
    hostname: str,
    files_synced: int = 0,
) -> Dict[str, Any]:
    uname = (username or "").strip().lower()
    host = (hostname or "").strip().upper()
    active_map: Dict[str, List[Dict[str, Any]]] = state.setdefault("active_sessions", {})
    sync_map: Dict[str, Dict[str, Any]] = state.setdefault("session_sync", {})

    remaining = [s for s in active_map.get(uname, []) if s.get("hostname") != host]
    if remaining:
        active_map[uname] = remaining
    else:
        active_map.pop(uname, None)

    now = datetime.datetime.now().isoformat(timespec="seconds")
    sync_map[uname] = {
        "last_machine": host,
        "last_sync_at": now,
        "files_synced": int(files_synced),
    }
    return {
        "status": "logged_out",
        "username": uname,
        "hostname": host,
        "last_machine": host,
        "last_sync_at": now,
        "remaining_sessions": remaining,
    }


def ensure_nas_user_home(username: str, password: Optional[str] = None) -> Dict[str, Any]:
    """
    Crée le dossier personnel permanent /srv/samba/homes/<uid> sur le serveur NAS
    et synchronise le compte Samba local si `smbpasswd` est disponible.
    Sans effet destructif sur Windows / en test unitaire.
    """
    import os
    import subprocess
    from pathlib import Path

    uid = (username or "").strip().lower()
    if not uid:
        return {"created": False}

    nas_root = Path(os.getenv("LYUX_NAS_ROOT", NAS_BASE))
    if os.name != "posix" or not nas_root.exists():
        return {"created": False, "path": f"{NAS_BASE}/homes/{uid}", "mode": "simulated"}

    home_dir = nas_root / "homes" / uid
    for sub in ("Documents", "Bureau", "Projets", ".config"):
        (home_dir / sub).mkdir(parents=True, exist_ok=True)

    if password and os.geteuid() == 0:
        subprocess.run(["useradd", "-M", "-d", f"/home/{uid}", "-s", "/bin/bash", uid], check=False)
        subprocess.run(["chpasswd"], input=f"{uid}:{password}\n", text=True, check=False)
        subprocess.run(["smbpasswd", "-a", "-s", uid], input=f"{password}\n{password}\n", text=True, check=False)
        subprocess.run(["chown", "-R", f"{uid}:{uid}", str(home_dir)], check=False)

    return {"created": True, "path": str(home_dir), "mode": "posix"}
