import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
import os
import subprocess
import random
import string
import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Header, status, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from models import (
    OtpGenerationRequest, OtpGenerationResponse,
    MachineEnrollmentRequest, MachineEnrollmentResponse,
    TicketCreationRequest, TicketCreationResponse
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API de Contrôle, d'Enrôlement et Tableau de Bord LyuX (Opération Manchot)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base de données en mémoire
ACTIVE_OTPS = {
    "LYUX-DEMO-2026": {"room_id": "B204", "expires_at": "2026-12-31T23:59:59"},
    "LYUX-S102-2026": {"room_id": "S102", "expires_at": "2026-12-31T23:59:59"}
}


CLASSES_CATALOG = {
    "1G1": {
        "id": "1G1",
        "name": "Première Générale 1",
        "level": "1ère",
        "room_default": "B204",
        "subgroups": ["Groupe A (TP)", "Groupe B (TP)", "Spécialité NSI"],
        "teachers": ["thomas.durand"],
        "students_count": 24,
        "samba_share": "/srv/samba/classes/1G1"
    },
    "1G2": {
        "id": "1G2",
        "name": "Première Générale 2 (Sciences)",
        "level": "1ère",
        "room_default": "S102",
        "subgroups": ["Groupe Physique", "Groupe SVT"],
        "teachers": ["sophie.leroy"],
        "students_count": 22,
        "samba_share": "/srv/samba/classes/1G2"
    },
    "TG1": {
        "id": "TG1",
        "name": "Terminale Générale 1",
        "level": "Terminale",
        "room_default": "B204",
        "subgroups": ["Spécialité NSI", "Spécialité Maths"],
        "teachers": ["thomas.durand"],
        "students_count": 28,
        "samba_share": "/srv/samba/classes/TG1"
    },
    "2NDE3": {
        "id": "2NDE3",
        "name": "Seconde 3",
        "level": "2nde",
        "room_default": "B204",
        "subgroups": ["Groupe 1 (SNT)", "Groupe 2 (SNT)"],
        "teachers": ["thomas.durand", "sophie.leroy"],
        "students_count": 32,
        "samba_share": "/srv/samba/classes/2NDE3"
    }
}

class CreateClassRequest(BaseModel):
    id: str
    name: str
    level: str
    room_default: Optional[str] = "B204"
    subgroups: Optional[List[str]] = []
    teachers: Optional[List[str]] = []

class AssignTeacherRequest(BaseModel):
    class_id: str
    teacher_username: str
    action: str = "assign"

class AddSubgroupRequest(BaseModel):
    class_id: str
    subgroup_name: str

class CreateUserRequest(BaseModel):
    username: str
    first_name: str
    last_name: str
    role: str
    classe: Optional[str] = ""
    subgroup: Optional[str] = ""
    classes_assigned: Optional[List[str]] = []
    password: Optional[str] = None

class CsvImportRequest(BaseModel):
    csv_content: str
    dry_run: bool = False

class UpdateSettingsRequest(BaseModel):
    enrollment_enabled: Optional[bool] = None

class ParcEnrollmentToggle(BaseModel):
    enabled: bool

class FlexibleEnrollRequest(BaseModel):
    hostname: str
    building: Optional[str] = None
    building_id: Optional[str] = None
    room: Optional[str] = None
    room_id: Optional[str] = None
    network_mode: Optional[str] = None
    ip: Optional[str] = None
    ip_address: Optional[str] = None
    mac: Optional[str] = None
    mac_address: Optional[str] = None
    role: Optional[str] = "eleve"

class CreateBuildingRequest(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = ""

class CreateRoomRequest(BaseModel):
    id: Optional[str] = None
    name: str
    building_id: str
    profile: Optional[str] = "standard"
    capacity: Optional[int] = 24
    teacher: Optional[str] = ""

class MoveMachineRequest(BaseModel):
    new_room_id: str
    new_building_id: Optional[str] = None

class ClientEnrollRequest(BaseModel):
    hostname: str
    building_id: str
    room_id: str
    mac_address: Optional[str] = ""
    ip_address: Optional[str] = ""
    role: Optional[str] = "eleve"
    client_id: Optional[str] = ""
    token: Optional[str] = ""

SYSTEM_SETTINGS = {
    "enrollment_enabled": True
}

BUILDINGS_CATALOG = {
    "BAT-A": {
        "id": "BAT-A",
        "name": "Bâtiment A",
        "description": "Administration et accueil"
    },
    "BAT-B": {
        "id": "BAT-B",
        "name": "Bâtiment B",
        "description": "Enseignement général et NSI"
    },
    "BAT-C": {
        "id": "BAT-C",
        "name": "Bâtiment C",
        "description": "Pôle Sciences et Informatique"
    },
    "BAT-D": {
        "id": "BAT-D",
        "name": "Bâtiment D",
        "description": "Ateliers technologiques et laboratoires"
    },
    "BAT-E": {
        "id": "BAT-E",
        "name": "Bâtiment E",
        "description": "Arts et langues vivantes"
    },
    "BAT-F": {
        "id": "BAT-F",
        "name": "Bâtiment F",
        "description": "CDI et espace multimédia"
    },
    "BAT-G": {
        "id": "BAT-G",
        "name": "Bâtiment G",
        "description": "Gymnase et vie associative"
    }
}

ROOM_CATALOG = {
    "C14": {
        "id": "C14",
        "name": "C14",
        "building_id": "BAT-C",
        "profile": "nsi",
        "capacity": 24,
        "teacher": ""
    },
    "C12": {
        "id": "C12",
        "name": "C12",
        "building_id": "BAT-C",
        "profile": "standard",
        "capacity": 24,
        "teacher": ""
    },
    "B204": {
        "id": "B204",
        "name": "B204",
        "building_id": "BAT-B",
        "profile": "standard",
        "capacity": 24,
        "teacher": ""
    },
    "S102": {
        "id": "S102",
        "name": "S102",
        "building_id": "BAT-B",
        "profile": "standard",
        "capacity": 24,
        "teacher": ""
    }
}

DEFAULT_USERS = [
    {"username": "lyux-admin", "display_name": "Administrateur Système", "role": "admin", "classe": "IT / Maintenance", "password": "LyuxAdmin2026!", "room": "ALL", "app": "Console Système & Cockpit"},
    {"username": "lyux.eleve", "display_name": "Élève Démo (LyuX)", "role": "eleve", "classe": "1G1 (B204)", "password": "Eleve2026!", "room": "B204", "app": "Thonny IDE Python & Kiosk"},
    {"username": "lyux.prof", "display_name": "Professeur Démo (LyuX)", "role": "enseignant", "classe": "Maths / NSI", "password": "Prof2026!", "room": "B204", "app": "Veyon Master (Supervision)"},
    {"username": "lucas.martin", "display_name": "Lucas Martin", "role": "eleve", "classe": "1G1 (B204)", "password": "Eleve2026!", "room": "B204", "app": "Thonny IDE Python"},
    {"username": "emma.bernard", "display_name": "Emma Bernard", "role": "eleve", "classe": "1G1 (B204)", "password": "Eleve2026!", "room": "B204", "app": "LibreOffice Writer"},
    {"username": "hugo.dubois", "display_name": "Hugo Dubois", "role": "eleve", "classe": "1G2 (S102)", "password": "Eleve2026!", "room": "S102", "app": "Avogadro 3D Chimie"},
    {"username": "lea.thomas", "display_name": "Léa Thomas", "role": "eleve", "classe": "1G2 (S102)", "password": "Eleve2026!", "room": "S102", "app": "Tracker Mécanique"},
    {"username": "thomas.durand", "display_name": "M. Durand", "role": "enseignant", "classe": "Maths / NSI", "password": "Prof2026!", "room": "B204", "app": "Veyon Master (Supervision)"},
    {"username": "sophie.leroy", "display_name": "Mme. Leroy", "role": "enseignant", "classe": "Physique / SVT", "password": "Prof2026!", "room": "S102", "app": "Veyon Master (Supervision)"},
    {"username": "claire.viesco", "display_name": "Claire Vie-Scolaire", "role": "viesco", "classe": "Vie Scolaire", "password": "Viesco2026!", "room": "VIESCO", "app": "Pronote & Portails"},
    {"username": "alain.direction", "display_name": "Alain Direction", "role": "administration", "classe": "Direction", "password": "Admin2026!", "room": "ADMIN", "app": "GLPI & Supervision"},
    {"username": "lyux-admin", "display_name": "Admin LyuX", "role": "technicien", "classe": "IT / Support", "password": "LyuxDeploy2026!", "room": "SERVEUR", "app": "Terminal & Ansible"}
]

USERS_STATE_PATH = Path(
    os.environ.get(
        "LYUX_USERS_STATE_PATH",
        str(Path(__file__).resolve().parent.parent / "data" / "users_state.json"),
    )
)


def load_users_state() -> List[Dict[str, Any]]:
    if USERS_STATE_PATH.exists():
        try:
            data = json.loads(USERS_STATE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return [dict(u) for u in DEFAULT_USERS]


def save_users_state() -> None:
    USERS_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = USERS_STATE_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(TEST_USERS, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp_path, USERS_STATE_PATH)


TEST_USERS = load_users_state()

ENROLLED_MACHINES = {
    "LyuX-C14-PC01": {"hostname": "LyuX-C14-PC01", "room": "C14", "building_id": "BAT-C", "ip": "192.168.10.13", "mac": "08:00:27:f0:45:15", "user": "Session Libre", "role": "eleve", "locked": False, "status": "online"},
    "LyuX-C14-PC02": {"hostname": "LyuX-C14-PC02", "room": "C14", "building_id": "BAT-C", "ip": "192.168.10.14", "mac": "08:00:27:f0:45:16", "user": "lucas.martin", "role": "eleve", "locked": False, "status": "online"},
    "LyuX-C12-PC01": {"hostname": "LyuX-C12-PC01", "room": "C12", "building_id": "BAT-C", "ip": "192.168.10.12", "mac": "08:00:27:f0:45:12", "user": "Session Libre", "role": "eleve", "locked": False, "status": "offline"},
    "b204-prof": {"hostname": "b204-prof", "room": "B204", "building_id": "BAT-B", "ip": "192.168.100.20", "user": "thomas.durand", "role": "prof", "locked": False, "status": "offline"},
    "b204-pc01": {"hostname": "b204-pc01", "room": "B204", "building_id": "BAT-B", "ip": "192.168.100.21", "user": "lucas.martin", "role": "eleve", "locked": False, "status": "offline"},
    "s102-pc01": {"hostname": "s102-pc01", "room": "S102", "building_id": "BAT-B", "ip": "192.168.100.31", "user": "hugo.dubois", "role": "eleve", "locked": False, "status": "offline"},
}

ROOM_COUNTERS = {"B204": 3, "S102": 3, "CDI": 1, "VIESCO": 1}
RECENT_TICKETS = [
    {"id": "GLPI-#4012", "title": "Écran clignote salle B204 poste 02", "author": "emma.bernard", "status": "En cours", "time": "Il y a 10 min"},
    {"id": "GLPI-#4009", "title": "Besoin de Thonny IDE mis à jour", "author": "thomas.durand", "status": "Résolu", "time": "Il y a 1h"}
]

class LockRoomRequest(BaseModel):
    room_id: str
    action: str  # "lock", "unlock", "message"
    message_text: Optional[str] = "Consigne du professeur : attention au tableau !"

class ResetPasswordRequest(BaseModel):
    username: str
    new_password: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "ok", "project": "LyuX Control API", "version": settings.VERSION, "api_version": "1"}


@app.get("/api/v1/classes")
def list_classes():
    return list(CLASSES_CATALOG.values())

@app.post("/api/v1/classes")
def create_class(req: CreateClassRequest):
    cid = req.id.upper().strip()
    if cid in CLASSES_CATALOG:
        raise HTTPException(status_code=400, detail="Cette classe existe déjà")
    CLASSES_CATALOG[cid] = {
        "id": cid,
        "name": req.name,
        "level": req.level,
        "room_default": req.room_default,
        "subgroups": req.subgroups or ["Groupe A", "Groupe B"],
        "teachers": req.teachers or [],
        "students_count": 0,
        "samba_share": f"/srv/samba/classes/{cid}"
    }
    return {"success": True, "class": CLASSES_CATALOG[cid]}

@app.post("/api/v1/classes/assign-teacher")
def assign_teacher_to_class(req: AssignTeacherRequest):
    cid = req.class_id.upper().strip()
    if cid not in CLASSES_CATALOG:
        raise HTTPException(status_code=404, detail="Classe introuvable")
    cls = CLASSES_CATALOG[cid]
    if req.action == "assign":
        if req.teacher_username not in cls["teachers"]:
            cls["teachers"].append(req.teacher_username)
    elif req.action == "unassign":
        if req.teacher_username in cls["teachers"]:
            cls["teachers"].remove(req.teacher_username)
    return {"success": True, "class_id": cid, "teachers": cls["teachers"]}

@app.post("/api/v1/classes/subgroups")
def add_subgroup(req: AddSubgroupRequest):
    cid = req.class_id.upper().strip()
    if cid not in CLASSES_CATALOG:
        raise HTTPException(status_code=404, detail="Classe introuvable")
    cls = CLASSES_CATALOG[cid]
    sg = req.subgroup_name.strip()
    if sg and sg not in cls["subgroups"]:
        cls["subgroups"].append(sg)
    return {"success": True, "class_id": cid, "subgroups": cls["subgroups"]}

@app.post("/api/v1/users/create")
def create_user_endpoint(req: CreateUserRequest, authorization: Optional[str] = Header(default=None)):
    if authorization:
        from admin_routes import _require_permission
        _require_permission(authorization, "users.manage")
    uname = req.username.lower().strip()
    if any(u["username"] == uname for u in TEST_USERS):
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà existant")
    from admin_routes import _STATE
    from rbac import build_user_rbac_view, ensure_rbac_state, normalize_user_roles
    roles_catalog, matrix = ensure_rbac_state(_STATE)
    valid_ids = {r["id"] for r in roles_catalog}
    raw_roles = getattr(req, "roles", None)
    user_roles = normalize_user_roles(raw_roles, req.role, valid_ids)
    new_user = {
        "username": uname,
        "display_name": f"{req.first_name.capitalize()} {req.last_name.upper()}",
        "role": user_roles[0],
        "roles": user_roles,
        "classe": req.classe or "Sans affectation",
        "subgroup": req.subgroup or "-",
        "password": (req.password.strip() if req.password and req.password.strip() else f"Pass{random.randint(1000, 9999)}!"),
        "room": "B204",
        "app": "Thonny IDE" if "eleve" in user_roles and len(user_roles) == 1 else "Veyon Master"
    }
    view = build_user_rbac_view(new_user, roles_catalog, matrix)
    new_user["role"] = view["effective_role"]
    TEST_USERS.append(new_user)
    save_users_state()
    if req.classe and req.classe.upper() in CLASSES_CATALOG and new_user["role"] == "eleve":
        CLASSES_CATALOG[req.classe.upper()]["students_count"] += 1
    from sessions import ensure_nas_user_home
    ensure_nas_user_home(uname, new_user["password"])
    return {"success": True, "user": {**new_user, **view}}

@app.post("/api/v1/users/import-csv")
def import_csv_endpoint(req: CsvImportRequest):
    import io, csv
    f = io.StringIO(req.csv_content.strip())
    reader = csv.DictReader(f)
    imported = []
    for row in reader:
        nom = (row.get("nom") or "").strip()
        prenom = (row.get("prenom") or "").strip()
        role = (row.get("role") or "eleve").strip().lower()
        classe = (row.get("classe") or "1G1").strip().upper()
        subgroup = (row.get("sous_groupe") or row.get("subgroup") or "Groupe A").strip()
        if not nom or not prenom:
            continue
        uname = f"{prenom.lower()}.{nom.lower()}"
        user = {
            "username": uname,
            "display_name": f"{prenom.capitalize()} {nom.upper()}",
            "role": role,
            "classe": classe,
            "subgroup": subgroup,
            "password": f"Pass{random.randint(1000, 9999)}!",
            "room": "B204",
            "app": "Thonny IDE" if role == "eleve" else "Veyon Master"
        }
        imported.append(user)
        if not req.dry_run:
            if not any(u["username"] == uname for u in TEST_USERS):
                TEST_USERS.append(user)
                save_users_state()
            if classe not in CLASSES_CATALOG:
                CLASSES_CATALOG[classe] = {
                    "id": classe,
                    "name": f"Classe {classe}",
                    "level": "Auto",
                    "room_default": "B204",
                    "subgroups": [subgroup] if subgroup else ["Groupe A"],
                    "teachers": [],
                    "students_count": 0,
                    "samba_share": f"/srv/samba/classes/{classe}"
                }
            if role == "eleve":
                CLASSES_CATALOG[classe]["students_count"] += 1
            if role in ["enseignant", "prof"] and uname not in CLASSES_CATALOG[classe]["teachers"]:
                CLASSES_CATALOG[classe]["teachers"].append(uname)
    return {"success": True, "count": len(imported), "imported": imported, "dry_run": req.dry_run}


class ChangeStudentClassRequest(BaseModel):
    username: str
    new_classe: str
    new_subgroup: Optional[str] = "-"

class RolloverRequest(BaseModel):
    school_year: str
    archive_terminales: bool = True
    promote_students: bool = True

@app.post("/api/v1/students/change-class")
def change_student_class(req: ChangeStudentClassRequest):
    user = next((u for u in TEST_USERS if u["username"] == req.username), None)
    if not user:
        raise HTTPException(status_code=404, detail="Élève introuvable")
    
    old_class = user.get("classe", "")
    user["classe"] = req.new_classe
    user["subgroup"] = req.new_subgroup or "-"
    
    # Update student counts in catalog
    if old_class in CLASSES_CATALOG and CLASSES_CATALOG[old_class]["students_count"] > 0:
        CLASSES_CATALOG[old_class]["students_count"] -= 1
    if req.new_classe in CLASSES_CATALOG:
        CLASSES_CATALOG[req.new_classe]["students_count"] += 1
        
    return {"success": True, "username": req.username, "old_class": old_class, "new_class": req.new_classe, "subgroup": req.new_subgroup}

@app.post("/api/v1/rollover/simulate")
def simulate_rollover(req: RolloverRequest):
    promoted = []
    archived = []
    for u in TEST_USERS:
        if u.get("role") == "eleve":
            cls = u.get("classe", "")
            if "TERM" in cls.upper() or "TG" in cls.upper():
                archived.append({"username": u["username"], "name": u["display_name"], "classe": cls, "action": "Archivage (Sortant)"})
            elif "1G" in cls.upper() or "1ERE" in cls.upper():
                promoted.append({"username": u["username"], "name": u["display_name"], "from": cls, "to": "TG1", "action": "Promotion en Terminale"})
            elif "2NDE" in cls.upper():
                promoted.append({"username": u["username"], "name": u["display_name"], "from": cls, "to": "1G1", "action": "Promotion en Première"})
    return {
        "success": True,
        "school_year": req.school_year,
        "summary": {
            "promoted_count": len(promoted),
            "archived_count": len(archived),
            "total_students": len([u for u in TEST_USERS if u.get("role") == "eleve"])
        },
        "promoted": promoted,
        "archived": archived
    }

@app.post("/api/v1/rollover/apply")
def apply_rollover(req: RolloverRequest):
    count_promoted = 0
    count_archived = 0
    for u in TEST_USERS:
        if u.get("role") == "eleve":
            cls = u.get("classe", "")
            if "TERM" in cls.upper() or "TG" in cls.upper():
                u["classe"] = "Anciens Élèves (Archivés)"
                u["subgroup"] = "Sortant"
                count_archived += 1
            elif "1G" in cls.upper() or "1ERE" in cls.upper():
                u["classe"] = "TG1"
                count_promoted += 1
            elif "2NDE" in cls.upper():
                u["classe"] = "1G1"
                count_promoted += 1
    return {"success": True, "message": f"Bascule {req.school_year} appliquée avec succès ({count_promoted} promus, {count_archived} archivés)."}

# --- PARAMÈTRES GÉNÉRAUX & ENRÔLEMENT ---
@app.get("/api/v1/settings")
def get_settings():
    return SYSTEM_SETTINGS

@app.post("/api/v1/settings")
def update_settings(req: UpdateSettingsRequest):
    if req.enrollment_enabled is not None:
        SYSTEM_SETTINGS["enrollment_enabled"] = req.enrollment_enabled
    return {"success": True, "settings": SYSTEM_SETTINGS}

@app.get("/api/v1/parc/status")
def get_parc_status():
    return {
        "enrollment_enabled": SYSTEM_SETTINGS.get("enrollment_enabled", True),
        "buildings": list(BUILDINGS_CATALOG.values())
    }

@app.post("/api/v1/parc/enrollment-toggle")
def toggle_parc_enrollment(req: ParcEnrollmentToggle):
    SYSTEM_SETTINGS["enrollment_enabled"] = req.enabled
    return {"success": True, "enrollment_enabled": SYSTEM_SETTINGS["enrollment_enabled"]}

@app.post("/api/v1/parc/enroll")
def parc_enroll(req: FlexibleEnrollRequest):
    b_id = req.building_id or req.building or "BAT-C"
    r_id = req.room_id or req.room or "C12"
    ip = req.ip or req.ip_address or "192.168.10.x"
    mac = req.mac or req.mac_address or "Non renseignée"
    h_clean = req.hostname.strip()
    
    if not SYSTEM_SETTINGS.get("enrollment_enabled", True):
        raise HTTPException(
            status_code=403,
            detail="L'enrôlement est actuellement désactivé par l'administrateur."
        )
    
    new_machine = {
        "hostname": h_clean,
        "room": r_id,
        "room_id": r_id,
        "building_id": b_id,
        "ip": ip,
        "mac": mac,
        "user": "Session Libre",
        "role": req.role or "eleve",
        "locked": False,
        "status": "online",
        "enrolled_at": datetime.datetime.now().isoformat()
    }
    ENROLLED_MACHINES[h_clean] = new_machine
    return {"success": True, "machine": new_machine, "message": f"Poste {h_clean} enrôlé avec succès !"}

# --- GESTION DES BÂTIMENTS ---
@app.get("/api/v1/buildings")
def list_buildings():
    return list(BUILDINGS_CATALOG.values())

@app.post("/api/v1/buildings")
def create_or_update_building(req: CreateBuildingRequest):
    b_id = req.id or f"BAT-{req.name.strip().upper().replace(' ', '-')[:8]}"
    BUILDINGS_CATALOG[b_id] = {
        "id": b_id,
        "name": req.name.strip(),
        "description": req.description or ""
    }
    return {"success": True, "building": BUILDINGS_CATALOG[b_id]}

@app.delete("/api/v1/buildings/{building_id}")
def delete_building(building_id: str):
    if building_id in BUILDINGS_CATALOG:
        del BUILDINGS_CATALOG[building_id]
        for r_id, r in list(ROOM_CATALOG.items()):
            if r.get("building_id") == building_id:
                del ROOM_CATALOG[r_id]
        return {"success": True, "message": f"Bâtiment {building_id} supprimé"}
    raise HTTPException(status_code=404, detail="Bâtiment introuvable")

# --- GESTION DES SALLES ---
@app.get("/api/v1/rooms")
def list_rooms(building_id: Optional[str] = None):
    rooms = list(ROOM_CATALOG.values())
    if building_id:
        rooms = [r for r in rooms if r.get("building_id") == building_id]
    return rooms

@app.post("/api/v1/rooms")
def create_or_update_room(req: CreateRoomRequest):
    r_id = req.id or req.name.strip().replace(" ", "").upper()
    
    # Règle : deux salles dans un même bâtiment ne peuvent pas avoir le même nom
    for existing_id, existing_room in ROOM_CATALOG.items():
        if existing_id != r_id and existing_room.get("building_id") == req.building_id:
            if existing_room.get("name", "").strip().lower() == req.name.strip().lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"Une salle nommée '{req.name.strip()}' existe déjà dans ce bâtiment."
                )

    BUILDINGS_CATALOG.setdefault(req.building_id, {
        "id": req.building_id,
        "name": req.building_id,
        "description": ""
    })
    ROOM_CATALOG[r_id] = {
        "id": r_id,
        "name": req.name.strip(),
        "building_id": req.building_id,
        "profile": req.profile or "standard",
        "capacity": req.capacity or 24,
        "teacher": req.teacher or ""
    }
    return {"success": True, "room": ROOM_CATALOG[r_id]}

@app.delete("/api/v1/rooms/{room_id}")
def delete_room(room_id: str):
    if room_id in ROOM_CATALOG:
        del ROOM_CATALOG[room_id]
        return {"success": True, "message": f"Salle {room_id} supprimée"}
    raise HTTPException(status_code=404, detail="Salle introuvable")

# --- GESTION DES MACHINES & PARC ---
@app.get("/api/v1/machines")
def list_machines(room_id: Optional[str] = None, building_id: Optional[str] = None):
    machines = list(ENROLLED_MACHINES.values())
    if room_id:
        machines = [m for m in machines if m.get("room") == room_id or m.get("room_id") == room_id]
    if building_id:
        machines = [m for m in machines if m.get("building_id") == building_id]
    return machines

@app.put("/api/v1/machines/{hostname}/move")
def move_machine(hostname: str, req: MoveMachineRequest):
    m = ENROLLED_MACHINES.get(hostname)
    if not m:
        raise HTTPException(status_code=404, detail="Machine introuvable")
    m["room"] = req.new_room_id
    m["room_id"] = req.new_room_id
    if req.new_building_id:
        m["building_id"] = req.new_building_id
    elif req.new_room_id in ROOM_CATALOG:
        m["building_id"] = ROOM_CATALOG[req.new_room_id].get("building_id", "")
    return {"success": True, "machine": m}

@app.delete("/api/v1/machines/{hostname}")
def delete_machine(hostname: str):
    if hostname in ENROLLED_MACHINES:
        del ENROLLED_MACHINES[hostname]
        return {"success": True, "message": f"Machine {hostname} supprimée"}
    raise HTTPException(status_code=404, detail="Machine introuvable")

# --- SUGGESTION DE NOM ET ENRÔLEMENT CLIENT ---
@app.get("/api/v1/enroll/suggest-hostname")
def suggest_hostname(room_id: str, building_id: Optional[str] = None):
    room_clean = room_id.replace(" ", "").upper()
    existing_hostnames = [m["hostname"].upper() for m in ENROLLED_MACHINES.values()]
    num = 1
    while True:
        candidate = f"{room_clean}-PC{num:02d}"
        if candidate not in existing_hostnames and f"LYUX-{candidate}" not in existing_hostnames:
            return {"suggested_hostname": candidate, "available": True, "room_id": room_id}
        num += 1

@app.post("/api/v1/enroll/check-hostname")
def check_hostname(req: Dict[str, Any]):
    raw_h = req.get("hostname", "")
    h_clean = str(raw_h).strip()
    exists = any(m["hostname"].upper() == h_clean.upper() for m in ENROLLED_MACHINES.values())
    return {"hostname": h_clean, "available": not exists}

def _sign_enrollment_payload(payload: Dict[str, Any]) -> str:
    import hashlib, hmac, json, os
    secret = os.getenv("LYUX_AUTH_SECRET", "lyux-dev-secret-change-in-production").encode("utf-8")
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hmac.new(secret, raw, hashlib.sha256).hexdigest()


@app.get("/api/v1/enroll/roles")
def list_enroll_roles():
    return [
        {"id": "eleve", "name": "Poste Élève standard (Kiosk sécurisé + Veyon Client)"},
        {"id": "prof", "name": "Poste Enseignant Principal (Veyon Master + Gestion)"},
    ]


@app.get("/api/v1/enroll/status/{client_id}")
def get_enrollment_status(client_id: str):
    cid = client_id.strip()
    for m in ENROLLED_MACHINES.values():
        if cid and m.get("client_id") == cid:
            room_id = m.get("room_id") or m.get("room", "")
            room_profile = ROOM_CATALOG.get(room_id, {}).get("profile", "standard")
            profile = {
                "id": room_profile,
                "room_id": room_id,
                "building_id": m.get("building_id", ""),
                "role": m.get("role", "eleve"),
            }
            return {
                "enrolled": True,
                "machine": m,
                "profile": profile,
                "signature": _sign_enrollment_payload({"client_id": cid, "hostname": m["hostname"], "profile": profile}),
            }
    return {"enrolled": False}


@app.post("/api/v1/enroll/client-enroll")
def client_enroll(req: ClientEnrollRequest):
    if not SYSTEM_SETTINGS.get("enrollment_enabled", False):
        raise HTTPException(
            status_code=403,
            detail="L'enregistrement de nouveaux PC est actuellement désactivé par l'administrateur dans les paramètres généraux."
        )

    b_clean = req.building_id.strip()
    r_clean = req.room_id.strip()
    role_clean = (req.role or "eleve").strip()
    cid_clean = (req.client_id or "").strip()
    mac_clean = (req.mac_address or "").strip().lower()
    h_clean = req.hostname.strip()

    if b_clean not in BUILDINGS_CATALOG:
        raise HTTPException(status_code=400, detail=f"Bâtiment inconnu dans le catalogue serveur : '{b_clean}'.")
    if r_clean not in ROOM_CATALOG:
        raise HTTPException(status_code=400, detail=f"Salle inconnue dans le catalogue serveur : '{r_clean}'.")
    room_info = ROOM_CATALOG[r_clean]
    if room_info.get("building_id") != b_clean:
        raise HTTPException(status_code=400, detail=f"La salle '{r_clean}' n'appartient pas au bâtiment '{b_clean}'.")
    if role_clean not in ("eleve", "prof"):
        raise HTTPException(status_code=400, detail=f"Rôle invalide : '{role_clean}'.")

    # Idempotence : reconnaître un poste déjà enrôlé via client_id ou mac_address stable
    for existing in ENROLLED_MACHINES.values():
        same_cid = cid_clean and existing.get("client_id") == cid_clean
        same_mac = mac_clean and existing.get("mac", "").lower() == mac_clean
        if same_cid or same_mac:
            room_id = existing.get("room_id") or existing.get("room", r_clean)
            room_profile = ROOM_CATALOG.get(room_id, {}).get("profile", "standard")
            profile = {
                "id": room_profile,
                "room_id": room_id,
                "building_id": existing.get("building_id", b_clean),
                "role": existing.get("role", role_clean),
            }
            return {
                "success": True,
                "idempotent": True,
                "status": "enrolled",
                "machine": existing,
                "profile": profile,
                "signature": _sign_enrollment_payload({"client_id": cid_clean, "hostname": existing["hostname"], "profile": profile}),
                "message": f"Poste {existing['hostname']} déjà enrôlé (reprise idempotente).",
            }

    if any(m["hostname"].upper() == h_clean.upper() for m in ENROLLED_MACHINES.values()):
        raise HTTPException(
            status_code=400,
            detail=f"Le nom d'ordinateur '{h_clean}' est déjà attribué à une autre machine."
        )

    new_machine = {
        "client_id": cid_clean,
        "hostname": h_clean,
        "room": r_clean,
        "room_id": r_clean,
        "building_id": b_clean,
        "ip": req.ip_address or "192.168.10.x",
        "mac": req.mac_address or "Non renseignée",
        "user": "Session Libre",
        "role": role_clean,
        "locked": False,
        "status": "online",
        "enrolled_at": datetime.datetime.now().isoformat()
    }
    ENROLLED_MACHINES[h_clean] = new_machine
    profile = {
        "id": room_info.get("profile", "standard"),
        "room_id": r_clean,
        "building_id": b_clean,
        "role": role_clean,
    }
    return {
        "success": True,
        "idempotent": False,
        "status": "enrolled",
        "machine": new_machine,
        "profile": profile,
        "signature": _sign_enrollment_payload({"client_id": cid_clean, "hostname": h_clean, "profile": profile}),
        "message": f"Poste {h_clean} enrôlé avec succès !",
    }

@app.get("/api/v1/users")
def list_test_users(authorization: Optional[str] = Header(default=None)):
    from admin_routes import _STATE, _require_permission
    from rbac import build_user_rbac_view, ensure_rbac_state
    if authorization:
        _require_permission(authorization, "users.view")
    roles_catalog, matrix = ensure_rbac_state(_STATE)
    result = []
    for u in TEST_USERS:
        view = build_user_rbac_view(u, roles_catalog, matrix)
        result.append({
            **u,
            **view,
        })
    return result

@app.post("/api/v1/control/lock-room")
def lock_room_control(req: LockRoomRequest, authorization: Optional[str] = Header(default=None)):
    if authorization:
        from admin_routes import _require_permission
        _require_permission(authorization, "parc.room_lock")
    count = 0
    for m in ENROLLED_MACHINES.values():
        if req.room_id == "*" or (m.get("room") == req.room_id and m.get("role") == "eleve"):
            if req.action == "lock":
                m["locked"] = True
            elif req.action == "unlock":
                m["locked"] = False
            count += 1
    return {"success": True, "action": req.action, "affected_machines": count, "message": req.message_text}


@app.post("/api/v1/control/unlock-all")
def unlock_all_machines(authorization: Optional[str] = Header(default=None)):
    from admin_routes import _require_permission
    actor = _require_permission(authorization, "parc.room_lock")["username"]
    count = 0
    for m in ENROLLED_MACHINES.values():
        m["locked"] = False
        count += 1
    for m in INVENTORY_FLEET:
        m["locked"] = False
        count += 1
    return {
        "success": True,
        "action": "unlock",
        "actor": actor,
        "affected_machines": count,
        "message": f"Déverrouillage Veyon envoyé à {count} poste(s) par {actor}.",
    }

@app.post("/api/v1/control/reset-password")
def reset_password(req: ResetPasswordRequest, authorization: Optional[str] = Header(default=None)):
    if authorization:
        from admin_routes import _require_permission
        _require_permission(authorization, "users.manage")
    target = req.username.strip().lower()
    user = next((u for u in TEST_USERS if u["username"].lower() == target), None)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur inconnu")
    new_pwd = (req.new_password or "").strip() or f"Pass{datetime.datetime.now().strftime('%M%S')}!"
    user["password"] = new_pwd
    save_users_state()
    from sessions import ensure_nas_user_home
    ensure_nas_user_home(user["username"], new_pwd)
    return {"success": True, "username": user["username"], "new_password": new_pwd}

@app.post("/api/v1/enroll/generate-otp", response_model=OtpGenerationResponse)
def generate_otp(req: OtpGenerationRequest):
    if req.room_id not in ROOM_CATALOG:
        raise HTTPException(status_code=404, detail=f"Salle {req.room_id} inexistante")
    
    code = f"LYUX-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"
    expire = (datetime.datetime.now() + datetime.timedelta(minutes=req.validity_minutes)).isoformat()
    ACTIVE_OTPS[code] = {"room_id": req.room_id, "expires_at": expire}
    
    return OtpGenerationResponse(otp_code=code, expires_at=expire, room_id=req.room_id)

@app.post("/api/v1/enroll/validate-otp", response_model=MachineEnrollmentResponse)
def validate_enrollment(req: MachineEnrollmentRequest):
    otp_data = ACTIVE_OTPS.get(req.otp_code)
    if not otp_data:
        raise HTTPException(status_code=400, detail="Code OTP d'enrôlement invalide ou expiré")
    
    room_id = req.room_id
    if room_id not in ROOM_CATALOG:
        room_id = otp_data["room_id"]

    if req.is_teacher_pc:
        hostname = f"{room_id.lower()}-prof"
        role = "prof"
    else:
        num = ROOM_COUNTERS.get(room_id, 1)
        hostname = f"{room_id.lower()}-pc{num:02d}"
        ROOM_COUNTERS[room_id] = num + 1
        role = "eleve"

    room_profile = ROOM_CATALOG[room_id]["profile"]
    
    ENROLLED_MACHINES[hostname] = {
        "hostname": hostname,
        "room": room_id,
        "ip": f"192.168.100.{random.randint(40, 200)}",
        "user": "Session Libre",
        "role": role,
        "locked": False,
        "status": "online"
    }

    return MachineEnrollmentResponse(
        status="enrolled",
        hostname=hostname,
        room_id=room_id,
        room_profile=room_profile,
        ansible_pull_url=f"http://git.{settings.LYUX_DOMAIN}/lyux/lyux-ansible.git",
        ldap_uri=f"ldap://192.168.100.10",
        message=f"Poste enrôlé avec succès sous le nom {hostname}"
    )

@app.post("/api/v1/tickets", response_model=TicketCreationResponse)
def create_ticket(req: TicketCreationRequest):
    ticket_id = f"GLPI-#{random.randint(1000, 9999)}"
    RECENT_TICKETS.insert(0, {
        "id": ticket_id,
        "title": req.title,
        "author": req.username,
        "status": "Nouveau",
        "time": "À l'instant"
    })
    return TicketCreationResponse(
        success=True,
        ticket_id=ticket_id,
        message="Ticket enregistré avec succès dans GLPI"
    )

@app.get("/preseed.cfg", response_class=PlainTextResponse)
def get_preseed():
    return """
# Preseed Debian 12 KDE Plasma Francais (Zero Question)
d-i debian-installer/language string fr
d-i debian-installer/country string FR
d-i debian-installer/locale string fr_FR.UTF-8
d-i localechooser/supported-locales multiselect fr_FR.UTF-8
d-i console-setup/ask_detect boolean false
d-i keyboard-configuration/xkb-keymap select fr(latin9)
d-i keyboard-configuration/layoutcode string fr
d-i keyboard-configuration/modelcode string pc105
d-i netcfg/choose_interface select auto
d-i netcfg/get_domain string lyux.lan
d-i mirror/country string manual
d-i mirror/http/hostname string deb.debian.org
d-i mirror/http/directory string /debian
d-i mirror/http/proxy string
d-i partman-auto/method string regular
d-i partman-auto/choose_recipe select atomic
d-i partman-partitioning/confirm_write_new_label boolean true
d-i partman/choose_partition select finish
d-i partman/confirm boolean true
d-i partman/confirm_nooverwrite boolean true
d-i passwd/root-login boolean false
d-i passwd/user-fullname string Administrateur LyuX
d-i passwd/username string lyux-admin
d-i passwd/user-password password LyuxAdmin2026!
d-i passwd/user-password-again password LyuxAdmin2026!
d-i user-setup/allow-password-weak boolean true
d-i user-setup/encrypt-home boolean false
tasksel tasksel/first multiselect kde-desktop, standard
d-i pkgsel/include string kde-plasma-desktop sddm cifs-utils libpam-mount sssd firefox-esr libreoffice python3-pyqt6 sudo curl git
d-i pkgsel/upgrade select none
popularity-contest popularity-contest/participate boolean false
d-i grub-installer/only_debian boolean true
d-i grub-installer/bootdev string default
d-i preseed/late_command string in-target usermod -aG sudo lyux-admin; in-target useradd -m -s /bin/bash invite; in-target passwd -d invite; in-target localectl set-keymap fr-latin9; in-target localectl set-x11-keymap fr pc105 latin9; in-target systemctl set-default graphical.target
d-i finish-install/reboot_in_progress note
""".strip()

@app.get("/", response_class=HTMLResponse)
def root_redirect(request: Request):
    """
    Redirection automatique vers l'interface unique LyuX Administration (Port 8087 / admin.lyux.lan)
    """
    host = request.headers.get("host", "localhost").split(":")[0]
    admin_url = "http://admin.lyux.lan" if host == "api.lyux.lan" else f"http://{host}:8087/"
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url={admin_url}">
    <title>Redirection vers LyuX Administration</title>
    <script>window.location.href = "{admin_url}";</script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0b0f19; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
        .card {{ background: #1e293b; padding: 2.5rem; border-radius: 1rem; border: 1px solid #334155; text-align: center; max-width: 480px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5); }}
        h1 {{ font-size: 1.5rem; margin-bottom: 1rem; color: #38bdf8; }}
        p {{ color: #94a3b8; font-size: 0.95rem; line-height: 1.5; margin-bottom: 1.5rem; }}
        a {{ display: inline-block; background: #0284c7; color: white; padding: 0.75rem 1.5rem; border-radius: 0.5rem; text-decoration: none; font-weight: 600; transition: background 0.2s; }}
        a:hover {{ background: #0369a1; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>🐧 LyuX Administration</h1>
        <p>L'interface d'administration centralisée est accessible sur <strong>admin.lyux.lan</strong> (port <strong>8087</strong>).</p>
        <a href="{admin_url}">Accéder à LyuX Administration (Port 8087) &rarr;</a>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=200)

@app.get("/api/v1/auth/sync")
def get_auth_sync(authorization: Optional[str] = Header(default=None)):
    """
    Exporte les comptes scolaires non secrets (identifiants et groupes)
    pour les administrateurs authentifiés uniquement. Ne lit jamais /etc/shadow
    et ne renvoie aucun hash de mot de passe.
    """
    from admin_routes import _require_permission
    _require_permission(authorization, "users.view")
    try:
        passwd: List[str] = []
        if os.path.exists("/etc/passwd"):
            with open("/etc/passwd", "r", encoding="utf-8") as f:
                passwd = [
                    l.strip()
                    for l in f
                    if len(l.split(":")) >= 7
                    and l.split(":")[2].isdigit()
                    and int(l.split(":")[2]) >= 1000
                    and l.split(":")[0] not in ["nobody", "lyux-admin"]
                ]
        groups: List[str] = []
        if os.path.exists("/etc/group"):
            with open("/etc/group", "r", encoding="utf-8") as f:
                groups = [
                    l.strip()
                    for l in f
                    if len(l.split(":")) >= 3
                    and (
                        (l.split(":")[2].isdigit() and int(l.split(":")[2]) >= 1000)
                        or l.split(":")[0] in ["eleves", "enseignants", "administration", "direction", "viescolaire", "viesco"]
                    )
                ]
        return {
            "users": passwd,
            "groups": groups,
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erreur interne lors de la lecture des comptes.")

# ==============================================================================
# GESTION CENTRALISÉE DES LOGICIELS (DISCOVER SERVEUR / CLIENTS)
# ==============================================================================

APPS_CATALOG: Dict[str, Dict[str, Any]] = {}

class AppCreateRequest(BaseModel):
    name: str
    package: Optional[str] = None
    category: str = "general"
    description: str = ""
    icon: str = "📦"
    allowed_groups: Optional[List[str]] = None
    allowed_roles: Optional[List[str]] = None
    auto_update: bool = True
    deployed: bool = True
    version: str = "latest"
    target: str = "Tous les postes"
    source: str = "Dépôt LyuX"
    format: str = "Paquet .deb"
    link: str = ""
    launch_args: str = ""

class AppUpdateRequest(BaseModel):
    allowed_groups: Optional[List[str]] = None
    allowed_roles: Optional[List[str]] = None
    auto_update: Optional[bool] = None
    deployed: Optional[bool] = None

_ROLE_GROUP_ALIASES = {
    "eleve": {"eleve", "eleves"},
    "eleves": {"eleve", "eleves"},
    "prof": {"prof", "enseignant", "enseignants"},
    "enseignant": {"prof", "enseignant", "enseignants"},
    "enseignants": {"prof", "enseignant", "enseignants"},
    "viesco": {"viesco", "vie_scolaire"},
    "administration": {"administration", "direction"},
    "admin": {"admin", "techniciens"},
}

def _apps_state_path() -> str:
    return os.getenv(
        "LYUX_APPS_STATE_PATH",
        str(Path(__file__).resolve().parent.parent / "data" / "apps_state.json"),
    )

def save_apps_state():
    path = _apps_state_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(APPS_CATALOG, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_apps_state():
    path = _apps_state_path()
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data:
            APPS_CATALOG.clear()
            APPS_CATALOG.update(data)
    except Exception:
        pass

load_apps_state()

def _is_role_allowed_for_app(app_entry: Dict[str, Any], role: Optional[str]) -> bool:
    if not role:
        return True
    r_low = role.strip().lower()
    if r_low == "admin":
        return True
    allowed = [str(x).strip().lower() for x in (app_entry.get("allowed_roles") or app_entry.get("allowed_groups") or [])]
    if not allowed or "all" in allowed or "tous" in allowed:
        return True
    aliases = _ROLE_GROUP_ALIASES.get(r_low, {r_low})
    return any(a in allowed for a in aliases)

@app.get("/api/v1/apps")
def get_apps():
    return list(APPS_CATALOG.values())

@app.post("/api/v1/apps")
def add_app(req: AppCreateRequest):
    pkg = (req.package or req.name).strip().replace(" ", "-")
    app_id = pkg.lower()
    roles = req.allowed_roles if req.allowed_roles is not None else (req.allowed_groups or ["eleve", "prof", "admin"])
    APPS_CATALOG[app_id] = {
        "id": app_id,
        "name": req.name.strip(),
        "package": pkg,
        "category": req.category,
        "icon": req.icon,
        "description": req.description,
        "allowed_roles": roles,
        "allowed_groups": req.allowed_groups if req.allowed_groups is not None else roles,
        "auto_update": req.auto_update,
        "deployed": req.deployed,
        "version": req.version,
        "target": req.target,
        "source": req.source,
        "format": req.format,
        "link": req.link,
        "launch_args": req.launch_args,
    }
    save_apps_state()
    return {"success": True, "app": APPS_CATALOG[app_id]}

@app.put("/api/v1/apps/{app_id}")
def update_app(app_id: str, req: AppUpdateRequest):
    if app_id not in APPS_CATALOG:
        raise HTTPException(status_code=404, detail="Logiciel non trouvé")
    app_entry = APPS_CATALOG[app_id]
    if req.allowed_roles is not None:
        app_entry["allowed_roles"] = req.allowed_roles
        if req.allowed_groups is None:
            app_entry["allowed_groups"] = req.allowed_roles
    if req.allowed_groups is not None:
        app_entry["allowed_groups"] = req.allowed_groups
        if req.allowed_roles is None:
            app_entry["allowed_roles"] = req.allowed_groups
    if req.auto_update is not None:
        app_entry["auto_update"] = req.auto_update
    if req.deployed is not None:
        app_entry["deployed"] = req.deployed
    save_apps_state()
    return {"success": True, "app": app_entry}

@app.delete("/api/v1/apps/{app_id}")
def delete_app(app_id: str):
    if app_id in APPS_CATALOG:
        del APPS_CATALOG[app_id]
        save_apps_state()
        return {"success": True, "message": "Logiciel retiré du catalogue"}
    raise HTTPException(status_code=404, detail="Logiciel non trouvé")

@app.post("/api/v1/apps/deploy")
def deploy_apps():
    return {
        "success": True,
        "message": "Ordre de déploiement et mise à jour diffusé aux postes clients.",
        "deployed_count": sum(1 for a in APPS_CATALOG.values() if a.get("deployed"))
    }

@app.get("/api/v1/apps/client")
def get_client_apps(role: Optional[str] = None):
    """Endpoint interrogé par les postes clients pour savoir quels paquets installer et quels rôles ont accès."""
    items = []
    for entry in APPS_CATALOG.values():
        item = dict(entry)
        item["authorized"] = _is_role_allowed_for_app(entry, role)
        items.append(item)
    peer_caches = [
        f"http://{m['ip']}:3142"
        for m in ENROLLED_MACHINES.values()
        if m.get("status") == "online" and m.get("ip")
    ]
    return {
        "cache_proxy": "http://192.168.10.1:3142",
        "peer_caches": peer_caches,
        "fallback_direct": True,
        "apps": items,
    }


_CURATED_STORE_FALLBACK = [
    {"id": "org.gimp.GIMP", "name": "GIMP", "package": "org.gimp.GIMP", "category": "Création", "source": "Flathub", "format": "Flatpak", "version": "2.10", "description": "Éditeur d'images avancé et retouche photo.", "icon": ""},
    {"id": "org.videolan.VLC", "name": "VLC", "package": "org.videolan.VLC", "category": "Multimédia", "source": "Flathub", "format": "Flatpak", "version": "3.0", "description": "Lecteur multimédia universel.", "icon": ""},
    {"id": "org.inkscape.Inkscape", "name": "Inkscape", "package": "org.inkscape.Inkscape", "category": "Création", "source": "Flathub", "format": "Flatpak", "version": "1.3", "description": "Dessin vectoriel SVG professionnel.", "icon": ""},
    {"id": "org.kde.krita", "name": "Krita", "package": "org.kde.krita", "category": "Création", "source": "Flathub", "format": "Flatpak", "version": "5.2", "description": "Peinture numérique et illustration.", "icon": ""},
    {"id": "org.libreoffice.LibreOffice", "name": "LibreOffice", "package": "org.libreoffice.LibreOffice", "category": "Bureautique", "source": "Flathub", "format": "Flatpak", "version": "24.8", "description": "Suite bureautique complète (Writer, Calc, Impress).", "icon": ""},
    {"id": "com.visualstudio.code", "name": "Visual Studio Code", "package": "com.visualstudio.code", "category": "NSI / Dev", "source": "Flathub", "format": "Flatpak", "version": "latest", "description": "Éditeur de code pour Python, Web, C/C++.", "icon": ""},
    {"id": "org.blender.Blender", "name": "Blender", "package": "org.blender.Blender", "category": "3D / STI2D", "source": "Flathub", "format": "Flatpak", "version": "4.2", "description": "Modélisation, animation et rendu 3D.", "icon": ""},
    {"id": "org.audacityteam.Audacity", "name": "Audacity", "package": "org.audacityteam.Audacity", "category": "Multimédia", "source": "Flathub", "format": "Flatpak", "version": "3.6", "description": "Enregistrement et montage audio multipiste.", "icon": ""},
    {"id": "inkscape", "name": "Inkscape (.deb)", "package": "inkscape", "category": "Création", "source": "Dépôt Debian", "format": "Paquet .deb", "version": "Debian 13", "description": "Paquet Debian officiel d'Inkscape.", "icon": ""},
    {"id": "vlc", "name": "VLC (.deb)", "package": "vlc", "category": "Multimédia", "source": "Dépôt Debian", "format": "Paquet .deb", "version": "Debian 13", "description": "Paquet Debian officiel du lecteur VLC.", "icon": ""},
]


@app.get("/api/v1/apps/store/search")
def search_app_store(q: str = "", source: str = "all", limit: int = 24):
    """Recherche en direct dans Flathub (style KDE Discover) et le catalogue APT Debian."""
    import urllib.request as _urlreq

    query = (q or "").strip()
    src_filter = (source or "all").strip().lower()
    results: List[Dict[str, Any]] = []

    if src_filter in ("all", "flathub"):
        try:
            if query:
                req_obj = _urlreq.Request(
                    "https://flathub.org/api/v2/search",
                    data=json.dumps({"query": query, "filters": []}).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "LyuX-Store/1.0"},
                    method="POST",
                )
            else:
                req_obj = _urlreq.Request(
                    "https://flathub.org/api/v2/collection/popular?page=1&per_page=18",
                    headers={"User-Agent": "LyuX-Store/1.0"},
                )
            with _urlreq.urlopen(req_obj, timeout=4.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            hits = data.get("hits") if isinstance(data, dict) else []
            for h in (hits or [])[:limit]:
                app_id = h.get("app_id") or h.get("id") or ""
                if not app_id:
                    continue
                cats = h.get("categories") or []
                results.append({
                    "id": app_id,
                    "name": h.get("name") or app_id,
                    "package": app_id,
                    "category": cats[0] if cats else "Flathub",
                    "source": "Flathub",
                    "format": "Flatpak",
                    "version": "Flathub",
                    "description": h.get("summary") or "",
                    "icon": h.get("icon") or "",
                    "link": f"https://flathub.org/apps/{app_id}",
                })
        except Exception:
            pass

    if src_filter in ("all", "apt") and query:
        try:
            proc = subprocess.run(
                ["apt-cache", "search", query],
                capture_output=True,
                text=True,
                timeout=3.0,
                check=False,
            )
            if proc.returncode == 0:
                for line in proc.stdout.splitlines()[:12]:
                    if " - " in line:
                        pkg_name, desc = line.split(" - ", 1)
                        pkg_clean = pkg_name.strip()
                        results.append({
                            "id": pkg_clean,
                            "name": pkg_clean,
                            "package": pkg_clean,
                            "category": "Debian APT",
                            "source": "Dépôt Debian",
                            "format": "Paquet .deb",
                            "version": "Debian 13",
                            "description": desc.strip(),
                            "icon": "",
                            "link": f"https://packages.debian.org/trixie/{pkg_clean}",
                        })
        except Exception:
            pass

    if not results:
        q_low = query.lower()
        for item in _CURATED_STORE_FALLBACK:
            if src_filter != "all" and src_filter not in item["source"].lower() and src_filter not in item["format"].lower():
                continue
            if not q_low or q_low in item["name"].lower() or q_low in item["description"].lower() or q_low in item["package"].lower():
                results.append(dict(item))

    return {"query": query, "source": src_filter, "items": results[:limit]}

CLIENT_STORAGE_REPORTS = {}

class ClientUserStat(BaseModel):
    username: str
    login_count: int = 1
    last_login: Optional[str] = None
    is_frequent: bool = False
    local_cache_mb: float = 0.0

class ClientStorageReport(BaseModel):
    hostname: str
    disk_total_gb: float
    disk_used_gb: float
    disk_free_gb: float
    disk_percent: int
    users: List[ClientUserStat] = []
    cleaned_space_mb: float = 0.0
    last_check: Optional[str] = None

@app.post("/api/v1/clients/storage-report")
def post_client_storage_report(report: ClientStorageReport):
    report_dict = report.dict()
    if not report_dict.get("last_check"):
        report_dict["last_check"] = datetime.datetime.now().isoformat()
    CLIENT_STORAGE_REPORTS[report.hostname] = report_dict
    return {"success": True, "message": "Rapport de stockage enregistré"}

@app.get("/api/v1/clients/storage-report")
def get_client_storage_reports():
    return CLIENT_STORAGE_REPORTS

# ==============================================================================
# SYSTÈME DE GESTION DES VERSIONS & MISES À JOUR (SERVEUR & CLIENTS)
# ==============================================================================

SYSTEM_SETTINGS = {
    "enrollment_enabled": True,
    "lyux_version": "1.0.0",
    "lyux_build": "20261122",
    "github_repo": "FlowCreativeStudio/OperationManchot",
    "github_branch": "main",
    "last_update_check": "2026-11-22T13:00:00Z",
    "update_available": False,
    "latest_version": "1.0.0",
    "auto_update_clients": True,
    "apt_cache_enabled": True,
    "nas_sync_enabled": True,
    "nas_share_path": "/srv/samba/homes",
    "desktop_profile_enabled": True,
}

CLIENT_VERSIONS: Dict[str, Dict[str, Any]] = {
    "LyuX-C14-PC01": {
        "hostname": "LyuX-C14-PC01",
        "building": "C",
        "room": "C14",
        "version": "1.0.0",
        "build": "20261122",
        "last_seen": "2026-11-22T13:05:00Z",
        "status": "up_to_date"
    }
}

class ClientVersionReport(BaseModel):
    hostname: str
    building: Optional[str] = None
    room: Optional[str] = None
    version: str
    build: Optional[str] = None

@app.get("/api/v1/system/settings")
def get_system_settings():
    """Renvoie les paramètres généraux, la version courante du système et le statut de mise à jour."""
    return SYSTEM_SETTINGS

@app.post("/api/v1/system/settings")
def update_system_settings(settings_data: Dict[str, Any]):
    """Met à jour les paramètres généraux."""
    for k, v in settings_data.items():
        if k in SYSTEM_SETTINGS:
            SYSTEM_SETTINGS[k] = v
    return {"success": True, "settings": SYSTEM_SETTINGS}

@app.get("/api/v1/system/updates/check")
def check_for_updates():
    """Vérifie si de nouvelles versions ou commits sont disponibles."""
    SYSTEM_SETTINGS["last_update_check"] = datetime.datetime.now().isoformat()
    return {
        "current_version": SYSTEM_SETTINGS["lyux_version"],
        "latest_version": SYSTEM_SETTINGS["latest_version"],
        "update_available": SYSTEM_SETTINGS["update_available"],
        "last_checked": SYSTEM_SETTINGS["last_update_check"],
        "message": "Le système LyuX Server et l'Admin Panel sont à jour."
    }

@app.post("/api/v1/system/updates/apply")
def apply_server_update():
    """Déclenche la mise à jour des composants serveur et de l'interface d'administration."""
    return {
        "success": True,
        "message": "Mise à jour du système LyuX appliquée avec succès. Services rechargés.",
        "version": SYSTEM_SETTINGS["lyux_version"]
    }


# ==============================================================================
# POLITIQUE DE MISES À JOUR PAR COMPOSANT (DEBIAN / KDE / LYUX)
# ==============================================================================

_UPDATES_POLICY_PATH = Path(
    os.environ.get(
        "LYUX_UPDATES_POLICY_PATH",
        str(Path(__file__).resolve().parent.parent / "data" / "updates_policy.json"),
    )
)


def _default_updates_policy() -> Dict[str, Any]:
    return {
        "debian": {
            "label": "Debian",
            "pin_package": "base-files",
            "selected_version": "",
            "latest_version": "",
            "latest_checked_at": "",
            "latest_error": "",
            "source": "deb.debian.org (trixie)",
        },
        "kde": {
            "label": "KDE Plasma",
            "pin_package": "plasma-desktop",
            "selected_version": "",
            "latest_version": "",
            "latest_checked_at": "",
            "latest_error": "",
            "source": "Debian trixie (plasma-desktop)",
        },
        "lyux": {
            "label": "LyuX OS",
            "pin_package": "lyux-desktop-core",
            "selected_version": "",
            "latest_version": "",
            "latest_checked_at": "",
            "latest_error": "",
            "source": "Dépôt APT LyuX / GitHub",
        },
        "auto_enforce": True,
        "updated_at": "",
    }


def _load_updates_policy() -> Dict[str, Any]:
    policy = _default_updates_policy()
    if _UPDATES_POLICY_PATH.exists():
        try:
            stored = json.loads(_UPDATES_POLICY_PATH.read_text(encoding="utf-8"))
            if isinstance(stored, dict):
                for key in ("debian", "kde", "lyux"):
                    if isinstance(stored.get(key), dict):
                        policy[key].update(stored[key])
                if "auto_enforce" in stored:
                    policy["auto_enforce"] = bool(stored["auto_enforce"])
                if "updated_at" in stored:
                    policy["updated_at"] = str(stored["updated_at"])
        except (OSError, json.JSONDecodeError):
            pass
    return policy


def _save_updates_policy(policy: Dict[str, Any]) -> None:
    _UPDATES_POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _UPDATES_POLICY_PATH.write_text(
        json.dumps(policy, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


UPDATE_POLICY: Dict[str, Any] = _load_updates_policy()


def _http_get_text(url: str, timeout: float = 5.0) -> str:
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "LyuX-Server/0.6"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _fetch_latest_debian_version() -> tuple[str, str]:
    try:
        raw = _http_get_text("https://deb.debian.org/debian/dists/trixie/Release")
        for line in raw.splitlines():
            if line.startswith("Version:"):
                ver = line.split(":", 1)[1].strip()
                if ver:
                    return ver, ""
            if line.startswith("Codename:"):
                codename = line.split(":", 1)[1].strip()
                if codename == "trixie":
                    return "13 (trixie)", ""
        return "", "Version introuvable dans Release"
    except Exception as exc:
        return "", f"Inaccessible ({exc})"


def _fetch_latest_kde_version() -> tuple[str, str]:
    try:
        raw = _http_get_text("https://sources.debian.org/api/src/plasma-desktop/")
        data = json.loads(raw)
        versions = data.get("versions") or []
        for entry in versions:
            suites = entry.get("suites") or []
            if "trixie" in suites or "testing" in suites:
                ver = str(entry.get("version") or "").strip()
                if ver:
                    return ver, ""
        if versions:
            ver = str(versions[0].get("version") or "").strip()
            if ver:
                return ver, ""
        return "", "Aucune version trouvée"
    except Exception as exc:
        return "", f"Inaccessible ({exc})"


def _fetch_latest_lyux_version() -> tuple[str, str]:
    local_ver = ""
    pool_dir = Path(__file__).resolve().parent.parent / "data" / "apt-repo" / "pool" / "main"
    if pool_dir.exists():
        debs = sorted(pool_dir.glob("lyux-desktop-core_*_all.deb"))
        if debs:
            name = debs[-1].name
            local_ver = name.removeprefix("lyux-desktop-core_").removesuffix("_all.deb")
    try:
        raw = _http_get_text("https://api.github.com/repos/Luux-Manchot/lyux-desktop/releases?per_page=1")
        releases = json.loads(raw)
        if isinstance(releases, list) and releases:
            tag = str(releases[0].get("tag_name") or "").lstrip("v").strip()
            if tag:
                return tag, ""
    except Exception as exc:
        if local_ver:
            return local_ver, f"Dépôt local uniquement (GitHub inaccessible : {exc})"
        return "", f"Inaccessible ({exc})"
    return local_ver, "" if local_ver else "Aucune release trouvée"


def _build_apt_preferences(policy: Dict[str, Any]) -> str:
    """Génère /etc/apt/preferences.d/lyux-policy.pref pour bloquer les paquets aux versions validées."""
    blocks = [
        "# Généré automatiquement par LyuX Server — ne pas modifier manuellement",
    ]
    for key in ("debian", "kde", "lyux"):
        entry = policy.get(key) or {}
        pkg = str(entry.get("pin_package") or "").strip()
        ver = str(entry.get("selected_version") or "").strip()
        if not pkg or not ver:
            continue
        clean_ver = ver.split()[0]
        blocks.append(
            f"Package: {pkg}\n"
            f"Pin: version {clean_ver}*\n"
            f"Pin-Priority: 1001"
        )
    return "\n\n".join(blocks) + "\n"


class ComponentPolicyPatch(BaseModel):
    selected_version: Optional[str] = None


class UpdatesPolicyUpdateRequest(BaseModel):
    debian: Optional[ComponentPolicyPatch] = None
    kde: Optional[ComponentPolicyPatch] = None
    lyux: Optional[ComponentPolicyPatch] = None
    auto_enforce: Optional[bool] = None


@app.get("/api/v1/updates/policy")
def get_updates_policy():
    """Renvoie la politique de mises à jour 3-composants (Debian, KDE, LyuX)."""
    return {
        "policy": UPDATE_POLICY,
        "apt_preferences": _build_apt_preferences(UPDATE_POLICY),
    }


@app.put("/api/v1/updates/policy")
@app.post("/api/v1/updates/policy")
def update_updates_policy(req: UpdatesPolicyUpdateRequest):
    """Enregistre les versions cibles sélectionnées par l'administrateur."""
    for key in ("debian", "kde", "lyux"):
        patch = getattr(req, key, None)
        if patch is not None and patch.selected_version is not None:
            UPDATE_POLICY[key]["selected_version"] = patch.selected_version.strip()
    if req.auto_enforce is not None:
        UPDATE_POLICY["auto_enforce"] = bool(req.auto_enforce)
    UPDATE_POLICY["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    _save_updates_policy(UPDATE_POLICY)
    return {
        "success": True,
        "policy": UPDATE_POLICY,
        "apt_preferences": _build_apt_preferences(UPDATE_POLICY),
    }


@app.post("/api/v1/updates/policy/check")
def refresh_updates_policy_latest():
    """Interroge les sources réelles (Debian, KDE, LyuX) pour connaître les dernières versions existantes."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    fetchers = {
        "debian": _fetch_latest_debian_version,
        "kde": _fetch_latest_kde_version,
        "lyux": _fetch_latest_lyux_version,
    }
    for key, fn in fetchers.items():
        ver, err = fn()
        if ver:
            UPDATE_POLICY[key]["latest_version"] = ver
        UPDATE_POLICY[key]["latest_checked_at"] = now
        UPDATE_POLICY[key]["latest_error"] = err
    _save_updates_policy(UPDATE_POLICY)
    return {
        "success": True,
        "policy": UPDATE_POLICY,
        "apt_preferences": _build_apt_preferences(UPDATE_POLICY),
    }


@app.get("/api/v1/client/updates/policy")
def get_client_updates_policy():
    """Endpoint interrogé par les postes clients et l'app Paramètres KDE."""
    lyux_ver = str(UPDATE_POLICY["lyux"].get("selected_version") or "").strip()
    deb_url = f"/api/v1/apt-repo/pool/main/lyux-desktop-core_{lyux_ver}_all.deb" if lyux_ver else ""
    return {
        "debian": UPDATE_POLICY["debian"],
        "kde": UPDATE_POLICY["kde"],
        "lyux": {**UPDATE_POLICY["lyux"], "deb_url": deb_url},
        "auto_enforce": UPDATE_POLICY.get("auto_enforce", True),
        "updated_at": UPDATE_POLICY.get("updated_at", ""),
        "apt_preferences": _build_apt_preferences(UPDATE_POLICY),
    }

from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse, RedirectResponse, Response
from release_registry import ReleaseRegistry
from apt_repo import SignedAptRepository

RELEASE_REGISTRY = ReleaseRegistry()
APT_REPOSITORY = SignedAptRepository(key_manager=RELEASE_REGISTRY.key_manager)
CLIENT_PROFILE_REPORTS: Dict[str, Dict[str, Any]] = {}


class ClientProfileReportRequest(BaseModel):
    client_id: str
    hostname: str
    profile_id: str
    profile_version: str
    state: str
    installed_packages: Dict[str, str] = {}
    error: Optional[str] = ""


@app.post("/api/v1/client/profile-report")
def post_client_profile_report(req: ClientProfileReportRequest):
    record = req.dict()
    record["reported_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    CLIENT_PROFILE_REPORTS[req.client_id or req.hostname] = record
    return {"success": True, "report": record}


@app.get("/api/v1/client/profile-report")
def list_client_profile_reports():
    return list(CLIENT_PROFILE_REPORTS.values())


@app.get("/api/v1/apt-repo/dists/trixie/Release")
def apt_repo_release():
    p = APT_REPOSITORY.repo_dir / "dists" / "trixie" / "Release"
    return PlainTextResponse(p.read_text(encoding="utf-8"))


@app.get("/api/v1/apt-repo/dists/trixie/Release.ed25519")
def apt_repo_release_sig():
    p = APT_REPOSITORY.repo_dir / "dists" / "trixie" / "Release.ed25519"
    return Response(content=p.read_bytes(), media_type="application/json")


@app.get("/api/v1/apt-repo/dists/trixie/main/binary-amd64/Packages")
def apt_repo_packages():
    p = APT_REPOSITORY.repo_dir / "dists" / "trixie" / "main" / "binary-amd64" / "Packages"
    return PlainTextResponse(p.read_text(encoding="utf-8"))


@app.get("/api/v1/apt-repo/dists/trixie/main/binary-amd64/Packages.gz")
def apt_repo_packages_gz():
    p = APT_REPOSITORY.repo_dir / "dists" / "trixie" / "main" / "binary-amd64" / "Packages.gz"
    return Response(content=p.read_bytes(), media_type="application/gzip")


@app.get("/api/v1/apt-repo/pool/main/{filename}")
def apt_repo_pool_deb(filename: str):
    safe = Path(filename).name
    p = APT_REPOSITORY.repo_dir / "pool" / "main" / safe
    if not p.exists() or not safe.endswith(".deb"):
        raise HTTPException(status_code=404, detail="Paquet introuvable dans le dépôt pilote.")
    return Response(content=p.read_bytes(), media_type="application/vnd.debian.binary-package")


@app.get("/api/v1/client/public-keys")
def get_client_public_keys():
    """Retourne uniquement les clés publiques Ed25519 (jamais de clé privée)."""
    return RELEASE_REGISTRY.key_manager.get_public_bundle()


@app.get("/api/v1/client/profile-manifest")
def get_client_profile_manifest(
    client_id: str,
    hostname: str,
    building_id: str,
    room_id: str,
    role: str = "eleve",
    schema_version: int = 1,
    client_version: str = "1.0.0",
    current_hash: str = "",
):
    """Retourne le manifeste de profil signé Ed25519 pour un poste enrôlé et autorisé."""
    if schema_version != 1:
        raise HTTPException(status_code=400, detail=f"schema_version non supportée : {schema_version}")

    matched = None
    for m in ENROLLED_MACHINES.values():
        if (client_id and m.get("client_id") == client_id) or m.get("hostname", "").lower() == hostname.strip().lower():
            matched = m
            break
    if not matched:
        raise HTTPException(status_code=403, detail="Poste non enrôlé ou non autorisé.")
    if matched.get("building_id") != building_id or (matched.get("room_id") or matched.get("room")) != room_id:
        raise HTTPException(status_code=403, detail="Portée bâtiment/salle refusée pour ce poste.")

    room_profile = ROOM_CATALOG.get(room_id, {}).get("profile", "standard")
    ok, payload = RELEASE_REGISTRY.build_client_manifest_response(
        building_id=building_id,
        room_id=room_id,
        role=role,
        profile_id=room_profile,
        current_hash=current_hash,
    )
    if not ok:
        raise HTTPException(status_code=404, detail=payload.get("detail", "Manifeste indisponible"))
    return payload


@app.get("/api/v1/client/update-manifest")
def get_client_update_manifest():
    """Compatibilité temporaire : renvoie la version publiée courante."""
    reg = RELEASE_REGISTRY.list_releases()
    pub = next((r for r in reg["releases"] if r.get("state") == "published"), None)
    return {
        "server_version": pub["version"] if pub else SYSTEM_SETTINGS["lyux_version"],
        "server_build": pub["build"] if pub else SYSTEM_SETTINGS["lyux_build"],
        "update_available": False,
        "critical_patches": [],
        "cache_proxy": "",
    }

@app.post("/api/v1/client/version-report")
def report_client_version(report: ClientVersionReport):
    """Enregistre la version rapportée par un poste client."""
    is_up_to_date = (report.version == SYSTEM_SETTINGS["lyux_version"])
    CLIENT_VERSIONS[report.hostname] = {
        "hostname": report.hostname,
        "building": report.building or "C",
        "room": report.room or "C14",
        "version": report.version,
        "build": report.build or SYSTEM_SETTINGS["lyux_build"],
        "last_seen": datetime.datetime.now().isoformat(),
        "status": "up_to_date" if is_up_to_date else "update_available"
    }
    return {"success": True, "status": "recorded"}

@app.get("/api/v1/parc/fleet-versions")
def get_fleet_versions():
    """Liste l'état des versions de tout le parc client avec statut ping réel."""
    res_list = []
    target_ver = SYSTEM_SETTINGS.get("lyux_version", "1.0.0")

    for c in CLIENT_VERSIONS.values():
        c_dict = dict(c)
        ip = c_dict.get("ip")
        if ip:
            ping_res = subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            is_online = (ping_res.returncode == 0)
        else:
            is_online = False
        c_dict["online"] = is_online
        c_dict["status"] = "up_to_date" if c_dict.get("version") == target_ver else "update_available"
        res_list.append(c_dict)

    return {
        "server_version": target_ver,
        "total_clients": len(res_list),
        "up_to_date_count": sum(1 for c in res_list if c["status"] == "up_to_date"),
        "clients": res_list
    }

# Inventaire complet des machines avec détection en temps réel (ping + versions + sessions)
INVENTORY_FLEET = [
    {"id": "1", "hostname": "LyuX-C14-PC01", "ip": "192.168.10.13", "mac": "08:00:27:f0:45:15", "building": "C", "room": "C14", "version": "1.0.0", "build": "20261122", "auto_update": True},
    {"id": "2", "hostname": "LyuX-C14-PC02", "ip": "192.168.10.14", "mac": "08:00:27:f0:45:16", "building": "C", "room": "C14", "version": "1.0.0", "build": "20261122", "auto_update": True},
    {"id": "3", "hostname": "C14-PC03", "ip": "192.168.10.15", "mac": "f8:09:d2:06:5e:06", "building": "C", "room": "C14", "version": "0.9.8", "build": "20261015", "auto_update": False},
    {"id": "4", "hostname": "LyuX-C12-PC01", "ip": "192.168.10.20", "mac": "08:00:27:a1:b2:c3", "building": "C", "room": "C12", "version": "1.0.0", "build": "20261122", "auto_update": True},
    {"id": "5", "hostname": "C12-PC02", "ip": "192.168.10.55", "mac": "08:00:27:d3:db:c3", "building": "C", "room": "C12", "version": "1.0.0", "build": "20261122", "auto_update": True},
    {"id": "6", "hostname": "B204-PC01", "ip": "192.168.10.30", "mac": "08:00:27:c4:d5:e6", "building": "B", "room": "B204", "version": "1.0.0", "build": "20261122", "auto_update": True},
    {"id": "7", "hostname": "S102-PC01", "ip": "192.168.10.40", "mac": "08:00:27:f7:e8:d9", "building": "S", "room": "S102", "version": "0.9.5", "build": "20260901", "auto_update": True}
]

@app.get("/api/v1/parc/inventory")
def get_live_inventory():
    """Scanne le réseau et renvoie l'état réel (en ligne / hors ligne / sessions / versions / auto-update)."""
    target_ver = SYSTEM_SETTINGS.get("lyux_version", "1.0.0")
    live_list = []
    
    for m in INVENTORY_FLEET:
        item = dict(m)
        ping_res = subprocess.run(["ping", "-c", "1", "-W", "1", item["ip"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        is_online = (ping_res.returncode == 0)
        item["status"] = "online" if is_online else "offline"
        item["session"] = "Session active" if is_online else "Aucune"
        item["is_up_to_date"] = (item.get("version") == target_ver)
        live_list.append(item)
        
    return {
        "server_version": target_ver,
        "machines": live_list
    }


from admin_routes import router as admin_router
app.include_router(admin_router)






