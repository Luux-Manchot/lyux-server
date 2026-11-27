"""
Schéma versionné de manifeste de profil LyuX et chaîne de confiance Ed25519.
Aucune clé privée n'est jamais embarquée dans le dépôt ou distribuée aux clients.
"""

import base64
import datetime
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

SCHEMA_NAME = "lyux-profile-manifest"
SCHEMA_VERSION = 1

STABLE_PROFILES = frozenset({
    "standard",
    "nsi",
    "sciences",
    "multimedia",
    "atelier",
    "prof",
    "eleve",
})

ALLOWED_ARTIFACT_TYPES = frozenset({
    "deb",
    "apt-repository",
    "flatpak",
    "theme",
    "kde-config",
    "kiosk-config",
    "veyon-config",
    "ansible-playbook-signed",
    "lyux-asset",
    "config",
    "ansible",
})

APPROVED_DEBIAN_PACKAGES = frozenset({
    "lyux-profile-standard",
    "lyux-profile-nsi",
    "lyux-profile-sciences",
    "lyux-profile-multimedia",
    "lyux-profile-atelier",
    "thonny",
    "geogebra",
    "veyon-service",
    "veyon-master",
    "firefox-esr-l10n-fr",
    "libreoffice-l10n-fr",
    "fonts-inter",
})

APPROVED_FLATPAKS = frozenset({
    "org.blender.Blender",
    "org.gimp.GIMP",
    "org.audacityteam.Audacity",
    "org.kde.krita",
})

RELEASE_STATES = frozenset({"draft", "signed", "published", "revoked", "removed"})

DEFAULT_APPROVED_SOURCES = (
    "https://deb.debian.org/",
    "https://flathub.org/",
    "https://github.com/Luux-Manchot/",
    "http://lyux-server",
    "https://lyux-server",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_SHELL_CHARS = (";", "|", "&", "`", "$(", "\n", "\r")


def get_approved_sources() -> Tuple[str, ...]:
    env_val = os.getenv("LYUX_APPROVED_SOURCES", "").strip()
    if env_val:
        return tuple(s.strip() for s in env_val.split(",") if s.strip())
    return DEFAULT_APPROVED_SOURCES


def is_approved_artifact_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    if any(ch in url for ch in _FORBIDDEN_SHELL_CHARS):
        return False
    return any(url.startswith(prefix) for prefix in get_approved_sources())


def canonical_manifest_bytes(manifest: Dict[str, Any]) -> bytes:
    """Sérialisation canonique du manifeste sans le champ signature."""
    payload = {k: v for k, v in manifest.items() if k != "signature"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def manifest_sha256(manifest: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_manifest_bytes(manifest)).hexdigest()


def _parse_iso(ts: str) -> datetime.datetime:
    dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


class Ed25519KeyManager:
    """Gère les clés Ed25519 de signature côté serveur (release & secours), hors dépôt."""

    def __init__(self, keys_dir: Optional[Path] = None):
        default_dir = os.getenv(
            "LYUX_KEYS_DIR",
            str(Path(__file__).resolve().parent.parent / "data" / "keys"),
        )
        self.keys_dir = Path(keys_dir or default_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.keyring_file = self.keys_dir / "keyring.json"
        self._ensure_active_key()

    def _priv_path(self, key_id: str) -> Path:
        return self.keys_dir / f"{key_id}.ed25519.priv.pem"

    def _pub_path(self, key_id: str) -> Path:
        return self.keys_dir / f"{key_id}.ed25519.pub.pem"

    def _load_keyring(self) -> Dict[str, Any]:
        if self.keyring_file.exists():
            return json.loads(self.keyring_file.read_text(encoding="utf-8"))
        return {"active_key_id": None, "backup_key_id": None, "keys": {}}

    def _save_keyring(self, data: Dict[str, Any]) -> None:
        tmp = self.keyring_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.keyring_file)

    def _generate_keypair(self, key_id: str) -> Tuple[str, str]:
        priv = ed25519.Ed25519PrivateKey.generate()
        pub = priv.public_key()
        priv_pem = priv.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        pub_pem = pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")
        self._priv_path(key_id).write_text(priv_pem, encoding="utf-8")
        try:
            os.chmod(self._priv_path(key_id), 0o600)
        except Exception:
            pass
        self._pub_path(key_id).write_text(pub_pem, encoding="utf-8")
        return priv_pem, pub_pem

    def _ensure_active_key(self) -> None:
        kr = self._load_keyring()
        active_id = kr.get("active_key_id")
        if active_id and self._priv_path(active_id).exists() and self._pub_path(active_id).exists():
            return
        now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        key_id = f"lyux-release-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}"
        _, pub_pem = self._generate_keypair(key_id)
        kr["active_key_id"] = key_id
        kr["keys"][key_id] = {
            "key_id": key_id,
            "role": "release",
            "status": "active",
            "created_at": now,
            "last_rotated_at": now,
            "public_key_pem": pub_pem,
        }
        self._save_keyring(kr)

    def rotate_key(self) -> Dict[str, Any]:
        """Effectue une rotation Ed25519 en conservant l'ancienne clé comme clé de secours."""
        kr = self._load_keyring()
        old_active = kr.get("active_key_id")
        now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        if old_active and old_active in kr.get("keys", {}):
            kr["keys"][old_active]["status"] = "backup"
            kr["backup_key_id"] = old_active

        new_id = f"lyux-release-{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        _, pub_pem = self._generate_keypair(new_id)
        kr["active_key_id"] = new_id
        kr["keys"][new_id] = {
            "key_id": new_id,
            "role": "release",
            "status": "active",
            "created_at": now,
            "last_rotated_at": now,
            "public_key_pem": pub_pem,
        }
        self._save_keyring(kr)
        return self.get_public_bundle()

    def sign_manifest(self, manifest: Dict[str, Any], key_id: Optional[str] = None) -> Tuple[str, str]:
        kr = self._load_keyring()
        kid = key_id or kr["active_key_id"]
        env_priv_pem = os.getenv("LYUX_RELEASE_PRIVATE_KEY_PEM", "").strip()
        if env_priv_pem:
            priv_bytes = env_priv_pem.encode("utf-8")
        else:
            priv_path = self._priv_path(kid)
            if not priv_path.exists():
                raise RuntimeError(f"Clé privée introuvable : {kid}")
            priv_bytes = priv_path.read_bytes()
        priv = serialization.load_pem_private_key(priv_bytes, password=None)
        sig_bytes = priv.sign(canonical_manifest_bytes(manifest))
        sig_b64 = base64.urlsafe_b64encode(sig_bytes).decode("ascii").rstrip("=")
        return sig_b64, kid

    def get_public_bundle(self) -> Dict[str, Any]:
        """Retourne uniquement les clés publiques (jamais de clé privée)."""
        kr = self._load_keyring()
        return {
            "active_key_id": kr.get("active_key_id"),
            "backup_key_id": kr.get("backup_key_id"),
            "keys": [
                {
                    "key_id": info["key_id"],
                    "role": info.get("role", "release"),
                    "status": info["status"],
                    "last_rotated_at": info.get("last_rotated_at", ""),
                    "public_key_pem": info["public_key_pem"],
                }
                for info in kr.get("keys", {}).values()
                if info.get("status") in ("active", "backup")
            ],
        }


def verify_ed25519_signature(manifest: Dict[str, Any], signature_b64: str, public_key_pem: str) -> bool:
    if not signature_b64 or not public_key_pem:
        return False
    try:
        padded = signature_b64 + "=" * (-len(signature_b64) % 4)
        sig_bytes = base64.urlsafe_b64decode(padded)
        pub = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        if not isinstance(pub, ed25519.Ed25519PublicKey):
            return False
        pub.verify(sig_bytes, canonical_manifest_bytes(manifest))
        return True
    except (InvalidSignature, ValueError, Exception):
        return False


def validate_manifest_contract(
    manifest: Dict[str, Any],
    public_keys: Dict[str, str],
    *,
    expected_scope: Optional[Dict[str, str]] = None,
    key_id: Optional[str] = None,
    now: Optional[datetime.datetime] = None,
) -> Tuple[bool, str]:
    """Valide schéma, portée, compatibilité, dates, artefacts et signature Ed25519."""
    if not isinstance(manifest, dict):
        return False, "Manifeste invalide (objet JSON requis)."

    if manifest.get("schema") != SCHEMA_NAME:
        return False, f"Schéma inconnu : {manifest.get('schema')}"
    if manifest.get("schema_version") != SCHEMA_VERSION:
        return False, f"Version de schéma non supportée : {manifest.get('schema_version')}"

    profile_id = manifest.get("profile_id")
    if profile_id not in STABLE_PROFILES:
        return False, f"Profil inconnu du catalogue : {profile_id}"

    if not manifest.get("profile_version"):
        return False, "profile_version manquant."

    # Validation temporelle (refuser expiré ou émis dans le futur)
    current = now or datetime.datetime.now(datetime.timezone.utc)
    try:
        issued = _parse_iso(str(manifest["issued_at"]))
        expires = _parse_iso(str(manifest["expires_at"]))
    except Exception:
        return False, "Horodatage issued_at/expires_at invalide."

    if issued > current + datetime.timedelta(seconds=60):
        return False, "Manifeste émis dans le futur refusé."
    if expires <= current:
        return False, "Manifeste expiré refusé."

    # Portée
    scope = manifest.get("scope")
    if not isinstance(scope, dict):
        return False, "Champ scope manquant."
    if expected_scope:
        for field in ("building_id", "room_id", "role"):
            if expected_scope.get(field) and scope.get(field) != expected_scope[field]:
                return False, f"Portée refusée sur {field} ({scope.get(field)} != {expected_scope[field]})."

    # Compatibilité système
    compat = manifest.get("compatibility")
    if not isinstance(compat, dict) or compat.get("debian") != "13" or compat.get("desktop") != "plasma6-x11":
        return False, "Compatibilité système refusée (Debian 13 / plasma6-x11 requis)."

    # Artefacts
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) == 0:
        return False, "Liste d'artefacts vide ou invalide."
    for art in artifacts:
        if not isinstance(art, dict):
            return False, "Artefact invalide."
        if "command" in art or "script" in art:
            return False, "Champ libre command/script interdit dans un manifeste."
        if art.get("type") not in ALLOWED_ARTIFACT_TYPES:
            return False, f"Type d'artefact interdit : {art.get('type')}"
        if art.get("type") == "deb" and art.get("package") and art["package"] not in APPROVED_DEBIAN_PACKAGES:
            return False, f"Paquet Debian hors catalogue approuvé : {art['package']}"
        if art.get("type") == "flatpak" and art.get("flatpak_id") and art["flatpak_id"] not in APPROVED_FLATPAKS:
            return False, f"Flatpak hors catalogue approuvé : {art['flatpak_id']}"
        if not is_approved_artifact_url(art.get("url", "")):
            return False, f"URL d'artefact non approuvée : {art.get('url')}"
        if not _SHA256_RE.match(str(art.get("sha256", ""))):
            return False, f"Empreinte SHA-256 invalide pour {art.get('name')}"
        if not isinstance(art.get("size"), int) or art["size"] <= 0:
            return False, f"Taille invalide pour {art.get('name')}"

    # Signature Ed25519
    sig = manifest.get("signature", "")
    if not sig:
        return False, "Signature Ed25519 absente."

    candidate_pems: List[str] = []
    if key_id and key_id in public_keys:
        candidate_pems.append(public_keys[key_id])
    else:
        candidate_pems.extend(public_keys.values())

    if not any(verify_ed25519_signature(manifest, sig, pem) for pem in candidate_pems):
        return False, "Signature Ed25519 invalide."

    return True, "OK"
