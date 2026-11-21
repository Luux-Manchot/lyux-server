import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import random
import string
import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
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

ROOM_CATALOG = {
    "B204": {
        "name": "Classe 1 — Salle Informatique NSI / Maths (1G1)",
        "profile": "nsi",
        "capacity": 24,
        "teacher": "M. Durand (Maths / NSI)"
    },
    "S102": {
        "name": "Classe 2 — Salle Sciences / Physique (1G2)",
        "profile": "sciences",
        "capacity": 24,
        "teacher": "Mme. Leroy (Sciences)"
    },
    "CDI": {
        "name": "Espace CDI / Travail Libre",
        "profile": "standard",
        "capacity": 15,
        "teacher": "Documentaliste"
    },
    "VIESCO": {
        "name": "Bureau Vie Scolaire & Accueil",
        "profile": "viesco",
        "capacity": 5,
        "teacher": "Claire CPE"
    }
}

TEST_USERS = [
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

ENROLLED_MACHINES = {
    "b204-prof": {"hostname": "b204-prof", "room": "B204", "ip": "192.168.100.20", "user": "thomas.durand", "role": "prof", "locked": False, "status": "online"},
    "b204-pc01": {"hostname": "b204-pc01", "room": "B204", "ip": "192.168.100.21", "user": "lucas.martin", "role": "eleve", "locked": False, "status": "online"},
    "b204-pc02": {"hostname": "b204-pc02", "room": "B204", "ip": "192.168.100.22", "user": "emma.bernard", "role": "eleve", "locked": False, "status": "online"},
    "s102-prof": {"hostname": "s102-prof", "room": "S102", "ip": "192.168.100.30", "user": "sophie.leroy", "role": "prof", "locked": False, "status": "online"},
    "s102-pc01": {"hostname": "s102-pc01", "room": "S102", "ip": "192.168.100.31", "user": "hugo.dubois", "role": "eleve", "locked": False, "status": "online"},
    "s102-pc02": {"hostname": "s102-pc02", "room": "S102", "ip": "192.168.100.32", "user": "lea.thomas", "role": "eleve", "locked": False, "status": "online"},
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

@app.get("/health")
def health_check():
    return {"status": "ok", "project": "LyuX Control API", "version": settings.VERSION}

@app.get("/api/v1/rooms")
def list_rooms():
    return ROOM_CATALOG

@app.get("/api/v1/users")
def list_test_users():
    return TEST_USERS

@app.get("/api/v1/machines")
def list_machines():
    return list(ENROLLED_MACHINES.values())

@app.post("/api/v1/control/lock-room")
def lock_room_control(req: LockRoomRequest):
    count = 0
    for m in ENROLLED_MACHINES.values():
        if m["room"] == req.room_id and m["role"] == "eleve":
            if req.action == "lock":
                m["locked"] = True
            elif req.action == "unlock":
                m["locked"] = False
            count += 1
    return {"success": True, "action": req.action, "affected_machines": count, "message": req.message_text}

@app.post("/api/v1/control/reset-password")
def reset_password(req: ResetPasswordRequest):
    user = next((u for u in TEST_USERS if u["username"] == req.username), None)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur inconnu")
    new_pwd = f"Pass{datetime.datetime.now().strftime('%M%S')}!"
    user["password"] = new_pwd
    return {"success": True, "username": req.username, "new_password": new_pwd}

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
def render_modern_dashboard():
    html_content = """<!DOCTYPE html>
<html lang="fr" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🐧 LyuX Hub — Opération Manchot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: {
                            500: '#0284c7',
                            600: '#0369a1',
                            dark: '#0f172a',
                            card: '#1e293b',
                            accent: '#38bdf8'
                        }
                    }
                }
            }
        }
    </script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        .glass { background: rgba(30, 41, 59, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .tab-active { background: #38bdf8; color: #0f172a; font-weight: 700; }
        .badge-pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
    </style>
</head>
<body class="bg-[#0b0f19] text-slate-100 min-h-screen flex flex-col">

    <!-- Header Navigation -->
    <header class="border-b border-slate-800 bg-[#0f172a]/90 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-2xl shadow-lg shadow-sky-500/20">
                    🐧
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <span class="text-xl font-bold tracking-tight text-white">LyuX Hub</span>
                        <span class="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 badge-pulse"></span> Serveur Actif (7 conteneurs)
                        </span>
                    </div>
                    <p class="text-xs text-slate-400">Opération Manchot • Migration Linux Lycée</p>
                </div>
            </div>

            <div class="flex items-center gap-3">
                <a href="/docs" target="_blank" class="text-xs text-slate-400 hover:text-sky-400 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/50 transition">
                    📖 API Swagger
                </a>
                <button onclick="switchTab('oobe')" class="flex items-center gap-1.5 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-slate-950 font-bold px-4 py-2 rounded-xl text-sm shadow-lg shadow-sky-500/20 transition transform active:scale-95">
                    <i data-lucide="zap" class="w-4 h-4"></i> Configuration Nouveau PC (OOBE)
                </button>
            </div>
        </div>
    </header>

    <!-- Navigation Tabs -->
    <nav class="border-b border-slate-800/80 bg-slate-900/40">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-1 sm:space-x-4 py-2 overflow-x-auto">
            <button onclick="switchTab('oobe')" id="tab-btn-oobe" class="tab-btn flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition text-slate-300 hover:text-white hover:bg-slate-800 tab-active">
                <i data-lucide="sparkles" class="w-4 h-4"></i> ⚙️ Assistant Nouveau PC (OOBE)
            </button>
            <button onclick="switchTab('classes')" id="tab-btn-classes" class="tab-btn flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition text-slate-300 hover:text-white hover:bg-slate-800">
                <i data-lucide="layout-grid" class="w-4 h-4"></i> 🏫 Supervision des 2 Classes
            </button>
            <button onclick="switchTab('users')" id="tab-btn-users" class="tab-btn flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition text-slate-300 hover:text-white hover:bg-slate-800">
                <i data-lucide="users" class="w-4 h-4"></i> 👥 Comptes & Mots de passe
            </button>
            <button onclick="switchTab('session')" id="tab-btn-session" class="tab-btn flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition text-slate-300 hover:text-white hover:bg-slate-800">
                <i data-lucide="monitor" class="w-4 h-4"></i> 💻 Simulateur KDE Plasma
            </button>
            <button onclick="switchTab('infra')" id="tab-btn-infra" class="tab-btn flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition text-slate-300 hover:text-white hover:bg-slate-800">
                <i data-lucide="server" class="w-4 h-4"></i> 📊 Services Docker & GLPI
            </button>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex-1 w-full">

        <!-- ================================================================= -->
        <!-- TAB 1: ASSISTANT OOBE STYLE WINDOWS SETUP (5 ÉTAPES)              -->
        <!-- ================================================================= -->
        <div id="tab-oobe" class="tab-content block space-y-6">
            <div class="max-w-2xl mx-auto">
                <div class="glass p-8 rounded-3xl space-y-6 shadow-2xl border border-sky-500/30">
                    
                    <!-- OOBE Wizard Step 1: Langue & Clavier -->
                    <div id="oobe-step-1" class="space-y-5">
                        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                            <div class="flex items-center gap-3">
                                <span class="text-2xl">🐧</span>
                                <h3 class="text-lg font-bold text-white">LyuX Setup — Préférences Régionales</h3>
                            </div>
                            <span class="text-xs font-bold text-sky-400 bg-sky-500/10 border border-sky-500/20 px-2.5 py-1 rounded-full">Étape 1 sur 3</span>
                        </div>

                        <p class="text-xs text-slate-400">Options par défaut pré-sélectionnées pour les établissements scolaires français. Vous pouvez les modifier :</p>

                        <div>
                            <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">🌐 Langue du système :</label>
                            <select id="oobe-lang" class="w-full bg-slate-800 border border-slate-700 rounded-xl p-3 text-sm text-white focus:ring-2 focus:ring-sky-500">
                                <option value="fr_FR" selected>🇫🇷 Français (France) [Par défaut]</option>
                                <option value="en_US">🇬🇧 English (US)</option>
                                <option value="es_ES">🇪🇸 Español</option>
                            </select>
                        </div>

                        <div>
                            <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">⌨️ Disposition du clavier :</label>
                            <select id="oobe-kbd" class="w-full bg-slate-800 border border-slate-700 rounded-xl p-3 text-sm text-white focus:ring-2 focus:ring-sky-500">
                                <option value="fr" selected>⌨️ Français AZERTY (latin9) [Par défaut]</option>
                                <option value="us">⌨️ Anglais QWERTY (US)</option>
                                <option value="be">⌨️ Belge AZERTY</option>
                            </select>
                        </div>

                        <div class="pt-3">
                            <button onclick="oobeGoToStep(2)" class="w-full py-3.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-sm shadow-lg shadow-sky-500/20 transition flex items-center justify-center gap-2">
                                Suivant (Serveur & Salle) <i data-lucide="arrow-right" class="w-4 h-4"></i>
                            </button>
                        </div>
                    </div>

                    <!-- OOBE Wizard Step 2: Serveur & Salle -->
                    <div id="oobe-step-2" class="hidden space-y-5">
                        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                            <div class="flex items-center gap-3">
                                <span class="text-2xl">📡</span>
                                <h3 class="text-lg font-bold text-white">Connexion Serveur & Attribution</h3>
                            </div>
                            <span class="text-xs font-bold text-sky-400 bg-sky-500/10 border border-sky-500/20 px-2.5 py-1 rounded-full">Étape 2 sur 3</span>
                        </div>

                        <div>
                            <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Adresse du Serveur LyuX :</label>
                            <div class="flex gap-2">
                                <input id="oobe-server-url" type="text" value="http://127.0.0.1:8000" class="flex-1 bg-slate-800 border border-slate-700 rounded-xl p-3 text-sm text-white font-mono">
                                <button onclick="testOobeServer()" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-xl text-xs font-semibold border border-slate-700 text-sky-400">
                                    🔍 Détecter
                                </button>
                            </div>
                            <p id="oobe-server-status" class="text-[11px] text-emerald-400 font-semibold mt-1.5 flex items-center gap-1">
                                <span class="w-2 h-2 rounded-full bg-emerald-400"></span> Serveur LyuX Détecté (API 1.0.0)
                            </p>
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">🏫 Salle / Classe :</label>
                                <select id="oobe-room" class="w-full bg-slate-800 border border-slate-700 rounded-xl p-3 text-sm text-white focus:ring-2 focus:ring-sky-500">
                                    <option value="B204">Classe 1 — Salle B204 (1G1 NSI)</option>
                                    <option value="S102">Classe 2 — Salle S102 (1G2 Sciences)</option>
                                    <option value="CDI">Espace CDI</option>
                                    <option value="VIESCO">Vie Scolaire</option>
                                </select>
                            </div>

                            <div>
                                <label class="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">💻 Type de poste :</label>
                                <select id="oobe-role" class="w-full bg-slate-800 border border-slate-700 rounded-xl p-3 text-sm text-white focus:ring-2 focus:ring-sky-500">
                                    <option value="student">Poste Élève standard</option>
                                    <option value="teacher">Poste Enseignant (Veyon Master)</option>
                                </select>
                            </div>
                        </div>

                        <div class="flex gap-3 pt-3">
                            <button onclick="oobeGoToStep(1)" class="w-1/3 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-sm transition">
                                ← Retour
                            </button>
                            <button onclick="startOobeInstallation()" class="w-2/3 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-extrabold text-sm shadow-lg shadow-emerald-500/20 transition flex items-center justify-center gap-2">
                                🚀 Lancer la Configuration <i data-lucide="zap" class="w-4 h-4"></i>
                            </button>
                        </div>
                    </div>

                    <!-- OOBE Wizard Step 3: Installation animée & Déploiement -->
                    <div id="oobe-step-3" class="hidden space-y-5">
                        <div class="text-center space-y-2">
                            <div class="w-12 h-12 rounded-2xl bg-sky-500/20 text-sky-400 flex items-center justify-center text-2xl mx-auto">
                                ⚡
                            </div>
                            <h3 class="text-xl font-bold text-white">Configuration du poste en cours...</h3>
                            <p class="text-xs text-slate-400">Installation des composants, rattachement LDAP et montages réseau</p>
                        </div>

                        <!-- Progress Bar -->
                        <div class="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                            <div id="oobe-progress-bar" class="bg-gradient-to-r from-sky-500 to-emerald-400 h-3 rounded-full transition-all duration-300" style="width: 10%"></div>
                        </div>

                        <!-- Step Checklist -->
                        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 font-mono text-xs text-slate-300 space-y-2">
                            <div id="step-chk-1" class="flex items-center gap-2 text-slate-500"><span>○</span> 1. Clavier Français AZERTY & Langue</div>
                            <div id="step-chk-2" class="flex items-center gap-2 text-slate-500"><span>○</span> 2. Raccordement Serveur & Jeton OTP</div>
                            <div id="step-chk-3" class="flex items-center gap-2 text-slate-500"><span>○</span> 3. Authentification LDAP / SSSD</div>
                            <div id="step-chk-4" class="flex items-center gap-2 text-slate-500"><span>○</span> 4. Montages CIFS (//homes, //classes)</div>
                            <div id="step-chk-5" class="flex items-center gap-2 text-slate-500"><span>○</span> 5. Attribution Nom d'Hôte & Profil Ansible</div>
                        </div>

                        <p id="oobe-install-status" class="text-center text-xs text-sky-400 font-semibold">Initialisation...</p>
                    </div>

                </div>
            </div>
        </div>

        <!-- ================================================================= -->
        <!-- TAB 2: SUPERVISION DES 2 CLASSES (VEYON MASTER SIMULATOR)        -->
        <!-- ================================================================= -->
        <div id="tab-classes" class="tab-content hidden space-y-6">
            <div class="glass p-5 rounded-2xl flex flex-wrap items-center justify-between gap-4">
                <div class="flex items-center gap-3">
                    <label class="text-sm text-slate-400 font-medium">Classe affichée :</label>
                    <select id="room-filter" onchange="renderRoomMachines()" class="bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-2 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-sky-500">
                        <option value="B204">Classe 1 — Salle B204 (1G1 - Informatique NSI / Maths)</option>
                        <option value="S102">Classe 2 — Salle S102 (1G2 - Sciences / Physique)</option>
                    </select>
                </div>

                <div class="flex items-center gap-2 flex-wrap">
                    <button onclick="controlClass('lock')" class="flex items-center gap-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 px-3.5 py-2 rounded-xl text-xs font-bold transition">
                        <i data-lucide="lock" class="w-4 h-4"></i> 🔒 Verrouiller la classe
                    </button>
                    <button onclick="controlClass('unlock')" class="flex items-center gap-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 px-3.5 py-2 rounded-xl text-xs font-bold transition">
                        <i data-lucide="unlock" class="w-4 h-4"></i> 🔓 Tout Déverrouiller
                    </button>
                    <button onclick="controlClass('message')" class="flex items-center gap-1.5 bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/40 px-3.5 py-2 rounded-xl text-xs font-bold transition">
                        <i data-lucide="message-square" class="w-4 h-4"></i> 💬 Diffuser consigne
                    </button>
                    <button onclick="switchTab('oobe')" class="flex items-center gap-1.5 bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/40 px-3.5 py-2 rounded-xl text-xs font-bold transition">
                        <i data-lucide="plus-circle" class="w-4 h-4"></i> + Nouveau PC
                    </button>
                </div>
            </div>

            <div id="machines-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5"></div>
        </div>

        <!-- ================================================================= -->
        <!-- TAB 3: ANNUAIRE DES COMPTES & MOTS DE PASSE                       -->
        <!-- ================================================================= -->
        <div id="tab-users" class="tab-content hidden space-y-6">
            <div class="glass p-6 rounded-3xl space-y-4">
                <div class="flex items-center justify-between flex-wrap gap-4">
                    <div>
                        <h2 class="text-xl font-bold text-white">Comptes de Test du Serveur LyuX</h2>
                        <p class="text-xs text-slate-400">Authentification centralisée LDAP/SSSD • Données sauvegardées sur le serveur</p>
                    </div>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="users-grid"></div>
            </div>
        </div>

        <!-- ================================================================= -->
        <!-- TAB 4: SIMULATEUR SESSION KDE PLASMA LIVE                         -->
        <!-- ================================================================= -->
        <div id="tab-session" class="tab-content hidden space-y-4">
            <div class="bg-[#181825] rounded-3xl overflow-hidden border border-slate-800 shadow-2xl flex flex-col min-h-[580px]">
                <div class="h-10 bg-[#11111B] border-b border-slate-800 px-4 flex items-center justify-between text-xs text-slate-300">
                    <div class="flex items-center gap-3">
                        <span class="font-bold text-sky-400">🐧 LyuX KDE Plasma</span>
                        <span class="text-slate-600">•</span>
                        <span id="session-top-badge" class="text-slate-400">Poste : b204-pc01 (Salle B204)</span>
                    </div>
                    <div class="flex items-center gap-4">
                        <span id="session-user-badge" class="font-semibold text-emerald-400">👤 Lucas Martin (1G1)</span>
                        <span id="clock-display" class="font-mono text-slate-400">14:32:00</span>
                        <button onclick="switchTab('users')" class="text-rose-400 hover:text-rose-300 font-bold px-2 py-0.5 rounded bg-rose-500/10 border border-rose-500/20">
                            Fermer Session
                        </button>
                    </div>
                </div>

                <div class="flex-1 p-6 relative flex flex-col justify-between bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-[#131722] to-[#0c0f17]">
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-2xl">
                        <button onclick="openPersonalShare()" class="p-4 rounded-2xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 flex flex-col items-center text-center gap-2 hover:border-sky-500/50 transition">
                            <span class="text-3xl">📁</span>
                            <span class="text-xs font-bold text-white">Espace Personnel</span>
                            <span class="text-[10px] text-slate-400">//serveur/homes</span>
                        </button>
                        <button onclick="openClassShare()" class="p-4 rounded-2xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 flex flex-col items-center text-center gap-2 hover:border-sky-500/50 transition">
                            <span class="text-3xl">📚</span>
                            <span class="text-xs font-bold text-white">Partage Classe</span>
                            <span class="text-[10px] text-slate-400">//serveur/classes</span>
                        </button>
                        <button onclick="openReportModal()" class="p-4 rounded-2xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 flex flex-col items-center text-center gap-2 hover:border-rose-500/50 transition">
                            <span class="text-3xl">🆘</span>
                            <span class="text-xs font-bold text-rose-300">Signaler Panne</span>
                            <span class="text-[10px] text-slate-400">Ticket GLPI</span>
                        </button>
                        <button onclick="openAppsMenu()" class="p-4 rounded-2xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 flex flex-col items-center text-center gap-2 hover:border-emerald-500/50 transition">
                            <span class="text-3xl">🚀</span>
                            <span class="text-xs font-bold text-white">Logiciels Lycée</span>
                            <span class="text-[10px] text-slate-400">Python, NSI, Sciences</span>
                        </button>
                    </div>

                    <div class="self-end bg-slate-900/90 border border-slate-800 p-4 rounded-2xl max-w-sm text-xs space-y-1 backdrop-blur shadow-xl">
                        <div class="flex items-center gap-2 text-emerald-400 font-bold">
                            <i data-lucide="shield-check" class="w-4 h-4"></i> Session Sécurisée LyuX
                        </div>
                        <p class="text-slate-400">Vos devoirs et documents sont synchronisés sur le stockage centralisé du lycée.</p>
                    </div>
                </div>

                <div class="h-12 bg-[#11111B] border-t border-slate-800 px-4 flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <button class="px-3 py-1.5 rounded-lg bg-sky-500 text-slate-950 font-extrabold text-xs flex items-center gap-1.5">
                            🐧 Menu LyuX
                        </button>
                        <div class="hidden sm:flex items-center gap-1 text-slate-400 text-xs px-3">
                            <span>Firefox</span> • <span>Thonny Python</span> • <span>LibreOffice</span>
                        </div>
                    </div>
                    <div class="text-xs text-slate-500">KDE Plasma 5.27 • Debian 12 Bookworm</div>
                </div>
            </div>
        </div>

        <!-- ================================================================= -->
        <!-- TAB 5: SERVICES SERVEUR & INFRASTRUCTURE                          -->
        <!-- ================================================================= -->
        <div id="tab-infra" class="tab-content hidden space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                <div class="glass p-5 rounded-2xl space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-sky-400 text-base">🌐 Traefik Reverse Proxy</span>
                        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300">PORT 8888</span>
                    </div>
                    <p class="text-xs text-slate-400">Routage dynamique des domaines .lyux.lan et gestion SSL/TLS.</p>
                    <a href="http://localhost:8888/dashboard/" target="_blank" class="block text-center text-xs font-bold text-sky-300 bg-sky-500/10 border border-sky-500/20 py-2 rounded-xl hover:bg-sky-500/20 transition">
                        Ouvrir Traefik Dashboard →
                    </a>
                </div>

                <div class="glass p-5 rounded-2xl space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-indigo-400 text-base">🎫 GLPI & Helpdesk</span>
                        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300">PORT 8085</span>
                    </div>
                    <p class="text-xs text-slate-400">Inventaire matériel des 2 classes et gestion des tickets d'incidents.</p>
                    <a href="http://localhost:8085" target="_blank" class="block text-center text-xs font-bold text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 py-2 rounded-xl hover:bg-indigo-500/20 transition">
                        Ouvrir Interface GLPI →
                    </a>
                </div>

                <div class="glass p-5 rounded-2xl space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-emerald-400 text-base">📡 Supervision Kuma</span>
                        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300">PORT 3001</span>
                    </div>
                    <p class="text-xs text-slate-400">Sonde de l'état des switchs, points d'accès Wi-Fi et serveurs.</p>
                    <a href="http://localhost:3001" target="_blank" class="block text-center text-xs font-bold text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 py-2 rounded-xl hover:bg-emerald-500/20 transition">
                        Ouvrir Supervision Uptime →
                    </a>
                </div>

                <div class="glass p-5 rounded-2xl space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-amber-400 text-base">⚡ Apt-Cacher-NG</span>
                        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300">PORT 3142</span>
                    </div>
                    <p class="text-xs text-slate-400">Cache local ultra rapide des paquets Debian pour les déploiements.</p>
                    <a href="http://localhost:3142/acng-report.html" target="_blank" class="block text-center text-xs font-bold text-amber-300 bg-amber-500/10 border border-amber-500/20 py-2 rounded-xl hover:bg-amber-500/20 transition">
                        Voir Rapport de Cache →
                    </a>
                </div>

                <div class="glass p-5 rounded-2xl space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-purple-400 text-base">🔑 LDAP Account Manager</span>
                        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300">PORT 8082</span>
                    </div>
                    <p class="text-xs text-slate-400">Gestion des utilisateurs, des classes et des quotas disques.</p>
                    <a href="http://localhost:8082" target="_blank" class="block text-center text-xs font-bold text-purple-300 bg-purple-500/10 border border-purple-500/20 py-2 rounded-xl hover:bg-purple-500/20 transition">
                        Accéder à LAM →
                    </a>
                </div>

                <div class="glass p-5 rounded-2xl space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-teal-400 text-base">⚙️ LyuX Control API</span>
                        <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300">PORT 8000</span>
                    </div>
                    <p class="text-xs text-slate-400">API FastAPI d'enrôlement OTP et pilotage pédagogique.</p>
                    <a href="/docs" target="_blank" class="block text-center text-xs font-bold text-teal-300 bg-teal-500/10 border border-teal-500/20 py-2 rounded-xl hover:bg-teal-500/20 transition">
                        Swagger Documentation →
                    </a>
                </div>
            </div>
        </div>

    </main>

    <!-- Modal Signaler Incident GLPI -->
    <div id="modal-report" class="fixed inset-0 bg-black/70 backdrop-blur-sm hidden flex items-center justify-center p-4 z-50">
        <div class="glass p-6 rounded-3xl max-w-lg w-full space-y-4 border border-rose-500/40">
            <div class="flex items-center justify-between">
                <h3 class="text-lg font-bold text-white flex items-center gap-2">
                    <span class="text-rose-400">🆘</span> Signaler un Problème Technique
                </h3>
                <button onclick="closeReportModal()" class="text-slate-400 hover:text-white">✕</button>
            </div>
            <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1">Titre de la panne :</label>
                <input id="ticket-title" type="text" placeholder="Ex: Clavier bloqué, écran noir..." class="w-full bg-slate-800 border border-slate-700 rounded-xl p-2.5 text-sm text-white">
            </div>
            <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1">Description :</label>
                <textarea id="ticket-desc" rows="3" placeholder="Expliquez ce qui se passe..." class="w-full bg-slate-800 border border-slate-700 rounded-xl p-2.5 text-sm text-white"></textarea>
            </div>
            <button onclick="submitTicket()" class="w-full py-3 bg-rose-500 hover:bg-rose-400 text-slate-950 font-bold rounded-xl text-sm transition">
                Envoyer le Ticket à l'équipe IT
            </button>
        </div>
    </div>

    <!-- JavaScript Logic -->
    <script>
        let currentActiveTab = 'oobe';
        let currentUser = null;
        let testUsers = [];
        let machinesList = [];

        window.addEventListener('DOMContentLoaded', async () => {
            lucide.createIcons();
            startClock();
            await fetchUsers();
            await fetchMachines();
            renderRoomMachines();
        });

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('tab-active'));

            const content = document.getElementById(`tab-${tabId}`);
            const btn = document.getElementById(`tab-btn-${tabId}`);
            if (content) content.classList.remove('hidden');
            if (btn) btn.classList.add('tab-active');
            currentActiveTab = tabId;

            if (tabId === 'classes') renderRoomMachines();
            if (tabId === 'users') renderUsersGrid();
            lucide.createIcons();
        }

        function oobeGoToStep(stepNum) {
            document.getElementById('oobe-step-1').classList.add('hidden');
            document.getElementById('oobe-step-2').classList.add('hidden');
            document.getElementById('oobe-step-3').classList.add('hidden');
            document.getElementById(`oobe-step-${stepNum}`).classList.remove('hidden');
            lucide.createIcons();
        }

        async function testOobeServer() {
            const url = document.getElementById('oobe-server-url').value;
            const statusEl = document.getElementById('oobe-server-status');
            statusEl.innerHTML = '<span class="text-sky-400">🔄 Test en cours...</span>';
            try {
                const res = await fetch('/health');
                if (res.ok) {
                    statusEl.innerHTML = '<span class="w-2 h-2 rounded-full bg-emerald-400 inline-block mr-1"></span> <span class="text-emerald-400">Serveur LyuX Détecté & En Ligne (API 1.0.0)</span>';
                }
            } catch(e) {
                statusEl.innerHTML = '<span class="text-amber-400">🟡 Serveur simulé en local</span>';
            }
        }

        async function startOobeInstallation() {
            oobeGoToStep(3);
            const pBar = document.getElementById('oobe-progress-bar');
            const statusTxt = document.getElementById('oobe-install-status');

            const setChk = (id, text, done = true) => {
                const el = document.getElementById(id);
                if (el) {
                    el.className = done ? "flex items-center gap-2 text-emerald-400 font-semibold" : "flex items-center gap-2 text-sky-400";
                    el.innerHTML = done ? `<span>✅</span> ${text}` : `<span>🔄</span> ${text}`;
                }
            };

            const room = document.getElementById('oobe-room').value;
            const isTeacher = document.getElementById('oobe-role').value === 'teacher';

            // Step 1
            pBar.style.width = '20%';
            setChk('step-chk-1', '1. Clavier Français AZERTY & Langue (OK)');
            statusTxt.innerText = "Configuration de la langue et du clavier...";
            await new Promise(r => setTimeout(r, 400));

            // Step 2
            pBar.style.width = '40%';
            setChk('step-chk-2', '2. Raccordement Serveur & Jeton OTP (OK)');
            statusTxt.innerText = "Validation du jeton OTP sur le serveur...";
            await new Promise(r => setTimeout(r, 400));

            // Step 3
            pBar.style.width = '65%';
            setChk('step-chk-3', '3. Authentification LDAP / SSSD (OK)');
            statusTxt.innerText = "Liaison au domaine scolaire lyux.lan...";
            await new Promise(r => setTimeout(r, 400));

            // Step 4
            pBar.style.width = '85%';
            setChk('step-chk-4', '4. Montages CIFS //homes et //classes (OK)');
            statusTxt.innerText = "Montage des disques réseau...";
            await new Promise(r => setTimeout(r, 400));

            // Server call
            try {
                const res = await fetch('/api/v1/enroll/validate-otp', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        otp_code: 'LYUX-DEMO-2026',
                        room_id: room,
                        mac_address: "52:54:00:" + Math.floor(Math.random()*89+10) + ":11:22",
                        is_teacher_pc: isTeacher
                    })
                });
                const data = await res.json();
                pBar.style.width = '100%';
                setChk('step-chk-5', `5. Machine prête : ${data.hostname} (OK)`);
                statusTxt.innerText = `🎉 Terminé ! Nom attribué : ${data.hostname}`;
                await fetchMachines();
                
                setTimeout(() => {
                    alert(`🎉 POSTE CONFIGURÉ AVEC SUCCÈS !\n\n• Nom d'hôte : ${data.hostname}\n• Salle : ${room}\n• Profil : ${data.room_profile}\n\nVous pouvez maintenant vous connecter avec n'importe quel compte.`);
                    switchTab('users');
                }, 700);
            } catch(e) {
                pBar.style.width = '100%';
                statusTxt.innerText = "Configuration terminée en mode local !";
                setTimeout(() => switchTab('users'), 700);
            }
        }

        function startClock() {
            setInterval(() => {
                const now = new Date();
                const str = now.toLocaleTimeString('fr-FR');
                const el = document.getElementById('clock-display');
                if (el) el.innerText = str;
            }, 1000);
        }

        async function fetchUsers() {
            try {
                const res = await fetch('/api/v1/users');
                testUsers = await res.json();
                currentUser = testUsers[0];
            } catch(e) {
                console.error(e);
            }
        }

        async function fetchMachines() {
            try {
                const res = await fetch('/api/v1/machines');
                machinesList = await res.json();
            } catch(e) {
                console.error(e);
            }
        }

        function renderRoomMachines() {
            const room = document.getElementById('room-filter').value;
            const container = document.getElementById('machines-grid');
            if (!container) return;

            const filtered = machinesList.filter(m => m.room === room);
            container.innerHTML = filtered.map(m => {
                const isProf = m.role === 'prof';
                const isLocked = m.locked;

                return `
                    <div class="glass p-5 rounded-2xl border ${isProf ? 'border-sky-500/40 bg-sky-950/20' : isLocked ? 'border-rose-500/60 bg-rose-950/20' : 'border-slate-800'} space-y-3 transition transform hover:scale-[1.01]">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span class="text-xl">${isProf ? '👨‍🏫' : '💻'}</span>
                                <div>
                                    <h4 class="font-bold text-white text-sm">${m.hostname}</h4>
                                    <p class="text-[11px] text-slate-400">${m.ip}</p>
                                </div>
                            </div>
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${isLocked ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'}">
                                ${isLocked ? '🔴 VERROUILLÉ' : '🟢 EN LIGNE'}
                            </span>
                        </div>

                        <div class="p-3 bg-slate-900/60 rounded-xl space-y-1 text-xs">
                            <div class="flex justify-between">
                                <span class="text-slate-400">Utilisateur :</span>
                                <span class="font-semibold text-sky-300">${m.user}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-slate-400">Rôle :</span>
                                <span class="capitalize text-slate-300">${m.role}</span>
                            </div>
                        </div>

                        <div class="flex items-center gap-2 pt-1">
                            <button onclick="launchSessionForUser('${m.user}')" class="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition">
                                🖥️ Voir l'écran
                            </button>
                            ${!isProf ? `
                                <button onclick="resetUserPwd('${m.user}')" class="px-2.5 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-xs font-semibold rounded-lg transition" title="Réinit Mot de Passe">
                                    🔑 MDP
                                </button>
                            ` : ''}
                        </div>
                    </div>
                `;
            }).join('');
            lucide.createIcons();
        }

        function renderUsersGrid() {
            const container = document.getElementById('users-grid');
            if (!container) return;

            container.innerHTML = testUsers.map(u => {
                const roleBadge = u.role === 'eleve' ? 'bg-sky-500/20 text-sky-300 border-sky-500/30'
                                : u.role === 'enseignant' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                                : 'bg-purple-500/20 text-purple-300 border-purple-500/30';

                return `
                    <div class="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl space-y-3 hover:border-slate-700 transition">
                        <div class="flex items-start justify-between">
                            <div>
                                <h4 class="font-bold text-white text-base">${u.display_name}</h4>
                                <span class="text-xs font-mono text-slate-400">${u.username}</span>
                            </div>
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold border ${roleBadge}">
                                ${u.role.toUpperCase()}
                            </span>
                        </div>

                        <div class="p-3 bg-slate-950/60 rounded-xl space-y-1.5 text-xs font-mono">
                            <div class="flex justify-between">
                                <span class="text-slate-500">Classe :</span>
                                <span class="text-slate-300">${u.classe}</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="text-slate-500">Mot de passe :</span>
                                <span class="text-emerald-400 font-bold bg-emerald-950/40 px-2 py-0.5 rounded">${u.password}</span>
                            </div>
                        </div>

                        <button onclick="launchSessionForUser('${u.username}')" class="w-full py-2 bg-gradient-to-r from-sky-500/20 to-blue-600/20 hover:from-sky-500/30 hover:to-blue-600/30 text-sky-300 border border-sky-500/40 rounded-xl text-xs font-bold transition">
                            💻 Tester la session KDE →
                        </button>
                    </div>
                `;
            }).join('');
        }

        async function controlClass(action) {
            const room = document.getElementById('room-filter').value;
            let msg = "Consigne du professeur : attention au tableau !";
            if (action === 'message') {
                const userMsg = prompt("Entrez le message à diffuser sur tous les écrans :", "Merci de vous concentrer sur l'exercice 3.");
                if (!userMsg) return;
                msg = userMsg;
            }

            try {
                const res = await fetch('/api/v1/control/lock-room', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({room_id: room, action: action, message_text: msg})
                });
                await fetchMachines();
                renderRoomMachines();

                if (action === 'message') {
                    alert(`💬 Message diffusé sur tous les postes de la salle ${room} :\n"${msg}"`);
                } else if (action === 'lock') {
                    alert(`🔒 Tous les postes élèves de la salle ${room} sont maintenant VERROUILLÉS !`);
                } else {
                    alert(`🔓 Tous les postes élèves de la salle ${room} sont DÉVERROUILLÉS !`);
                }
            } catch(e) {
                alert("Erreur lors de la commande Veyon.");
            }
        }

        async function resetUserPwd(login) {
            try {
                const res = await fetch('/api/v1/control/reset-password', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: login})
                });
                const data = await res.json();
                alert(`🔑 Mot de passe réinitialisé avec succès pour ${login} !\n\nNouveau mot de passe : ${data.new_password}`);
                await fetchUsers();
                if (currentActiveTab === 'users') renderUsersGrid();
            } catch(e) {
                alert("Erreur de réinitialisation.");
            }
        }

        function launchSessionForUser(login) {
            const user = testUsers.find(u => u.username === login || u.display_name === login) || testUsers[0];
            currentUser = user;
            document.getElementById('session-user-badge').innerText = `👤 ${user.display_name} (${user.role.toUpperCase()})`;
            document.getElementById('session-top-badge').innerText = `Poste : ${user.room.toLowerCase()}-pc01 • Salle ${user.room}`;
            switchTab('session');
        }

        function openPersonalShare() {
            alert(`📁 Espace Personnel Réseau //serveur.lyux.lan/homes/${currentUser.username}\n\nFichiers synchronisés :\n• devoir_nsi.py\n• presentation_sciences.odp\n• tp_mesures.calc\n\n✅ Sauvegarde automatique sur le serveur.`);
        }

        function openClassShare() {
            alert(`📚 Partage Classe //serveur.lyux.lan/classes/${currentUser.room}\n\nDossiers accessibles :\n• 📥 [Dépôt Devoirs] (Écriture seule)\n• 📖 [Documents de Cours] (Lecture seule)\n• 💡 [Ressources TP]`);
        }

        function openAppsMenu() {
            alert(`🚀 Logiciels disponibles dans le profil LyuX :\n• Thonny Python IDE\n• VS Code / VSCodium\n• LibreOffice 7.5\n• GIMP & Inkscape\n• Avogadro & Tracker 3D`);
        }

        function openReportModal() {
            document.getElementById('modal-report').classList.remove('hidden');
        }

        function closeReportModal() {
            document.getElementById('modal-report').classList.add('hidden');
        }

        async function submitTicket() {
            const title = document.getElementById('ticket-title').value;
            const desc = document.getElementById('ticket-desc').value;
            if (!title) return alert("Veuillez saisir un titre.");

            try {
                const res = await fetch('/api/v1/tickets', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        title: title,
                        category: 'Materiel',
                        description: desc,
                        hostname: `${currentUser.room.toLowerCase()}-pc01`,
                        username: currentUser.username
                    })
                });
                const data = await res.json();
                alert(`✅ Ticket ${data.ticket_id} créé dans GLPI avec succès !`);
                closeReportModal();
                document.getElementById('ticket-title').value = '';
                document.getElementById('ticket-desc').value = '';
            } catch(e) {
                alert("Erreur lors de la création du ticket.");
            }
        }
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)
