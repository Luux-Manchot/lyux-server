"""
Registre atomique et thread-safe des releases et manifestes de profils signés Ed25519.
Remplace les données simulées par un cycle de vie réel :
  draft -> signed -> published -> revoked / removed
"""

import datetime
import hashlib
import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from profile_trust import (
    Ed25519KeyManager,
    RELEASE_STATES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STABLE_PROFILES,
    is_approved_artifact_url,
    manifest_sha256,
    validate_manifest_contract,
    verify_ed25519_signature,
)


class ReleaseRegistry:
    def __init__(self, data_dir: Optional[Path] = None, keys_dir: Optional[Path] = None):
        default_dir = os.getenv(
            "LYUX_DATA_DIR",
            "/app/data" if Path("/app/data").exists() else str(Path(__file__).resolve().parent.parent / "data"),
        )
        self.data_dir = Path(data_dir or default_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.data_dir / "releases_registry.json"
        self.key_manager = Ed25519KeyManager(keys_dir=keys_dir or (self.data_dir / "keys"))
        self._lock = threading.RLock()
        self._state = self._load_or_init()

    def _atomic_save(self) -> None:
        tmp = self.registry_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._state, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.registry_file)

    def _build_default_manifest(self, profile_id: str, version: str, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        now = datetime.datetime.now(datetime.timezone.utc)
        return {
            "schema": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "profile_id": profile_id,
            "profile_version": version,
            "issued_at": (now - datetime.timedelta(seconds=5)).isoformat(timespec="seconds"),
            "expires_at": (now + datetime.timedelta(days=30)).isoformat(timespec="seconds"),
            "scope": {"building_id": "*", "room_id": "*", "role": "*"},
            "artifacts": artifacts,
            "compatibility": {"debian": "13", "desktop": "plasma6-x11", "lyux_client_min": "1.0.0"},
        }

    def _load_or_init(self) -> Dict[str, Any]:
        with self._lock:
            if self.registry_file.exists():
                try:
                    data = json.loads(self.registry_file.read_text(encoding="utf-8"))
                    if isinstance(data, dict) and "releases" in data:
                        return data
                except Exception:
                    pass

            # Initialisation réelle signée avec la clé Ed25519 du serveur
            base_art = {
                "id": "lyux-base-profile",
                "type": "config",
                "name": "lyux-desktop-profile-1.0.0.json",
                "url": "https://github.com/Luux-Manchot/lyux-desktop/releases/download/v1.0.0/lyux-desktop-profile-1.0.0.json",
                "sha256": hashlib.sha256(b"lyux-desktop-profile-1.0.0").hexdigest(),
                "size": 4096,
            }
            m_base = self._build_default_manifest("standard", "1.0.0", [base_art])
            sig, kid = self.key_manager.sign_manifest(m_base)
            m_base["signature"] = sig
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
            state = {
                "releases": [
                    {
                        "id": "rel-1.0.0",
                        "version": "1.0.0",
                        "build": "20261125",
                        "channel": "stable",
                        "family": "client",
                        "profile_id": "standard",
                        "state": "published",
                        "target": "Catalogue contrôlé",
                        "author": "system",
                        "notes": "Socle profil Debian 13 Plasma6-X11 signé Ed25519.",
                        "released_at": now_iso,
                        "published_at": now_iso,
                        "key_id": kid,
                        "signature": "Vérifiée",
                        "detached_signature": sig,
                        "manifest_hash": manifest_sha256(m_base),
                        "manifest": m_base,
                        "artifacts": [base_art],
                    }
                ],
                "policy": {
                    "channel": "stable",
                    "auto_update": True,
                    "update_window": "22:00 – 05:00",
                    "require_signed": True,
                    "canary_room": "C14",
                },
                "audit_log": [
                    {
                        "timestamp": now_iso,
                        "actor": "system",
                        "action": "init_published",
                        "release_id": "rel-1.0.0",
                        "detail": f"Initialisation signée Ed25519 ({kid})",
                    }
                ],
            }
            self._state = state
            self._atomic_save()
            return state

    def _record_audit(self, actor: str, action: str, release_id: str, detail: str) -> None:
        self._state.setdefault("audit_log", []).insert(0, {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "actor": actor,
            "action": action,
            "release_id": release_id,
            "detail": detail,
        })
        self._state["audit_log"] = self._state["audit_log"][:200]

    def list_releases(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "releases": list(self._state.get("releases", [])),
                "policy": dict(self._state.get("policy", {})),
                "public_keys": self.key_manager.get_public_bundle(),
                "audit_log": list(self._state.get("audit_log", []))[:50],
            }

    def get_release(self, release_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return next((r for r in self._state.get("releases", []) if r["id"] == release_id), None)

    def create_draft(
        self,
        *,
        version: str,
        profile_id: str = "standard",
        channel: str = "stable",
        family: str = "client",
        notes: str = "",
        artifacts: Optional[List[Dict[str, Any]]] = None,
        actor: str = "admin",
    ) -> Tuple[bool, Any]:
        with self._lock:
            pid = profile_id.strip()
            if pid not in STABLE_PROFILES:
                return False, f"Profil inconnu : {pid}"
            ver = version.strip()
            if not ver:
                return False, "Version requise."
            rel_id = f"rel-{pid}-{ver}"
            if self.get_release(rel_id):
                return False, f"La release {rel_id} existe déjà."

            norm_artifacts: List[Dict[str, Any]] = []
            for idx, art in enumerate(artifacts or []):
                url = str(art.get("url", "")).strip()
                if not is_approved_artifact_url(url):
                    return False, f"URL d'artefact non approuvée : {url}"
                content_raw = art.get("content")
                if content_raw is not None:
                    raw_bytes = content_raw.encode("utf-8") if isinstance(content_raw, str) else bytes(content_raw)
                    sha = hashlib.sha256(raw_bytes).hexdigest()
                    size = len(raw_bytes)
                else:
                    sha = str(art.get("sha256", "")).strip().lower()
                    size = int(art.get("size", 0))
                if len(sha) != 64 or size <= 0:
                    return False, f"Empreinte SHA-256 ou taille invalide pour {art.get('name', idx)}."
                norm_art: Dict[str, Any] = {
                    "id": art.get("id") or f"{rel_id}-art-{idx + 1}",
                    "type": art.get("type", "config"),
                    "name": art.get("name", f"artifact-{idx + 1}"),
                    "url": url,
                    "sha256": sha,
                    "size": size,
                }
                for opt_field in ("package", "flatpak_id", "version", "architecture"):
                    if art.get(opt_field):
                        norm_art[opt_field] = str(art[opt_field]).strip()
                norm_artifacts.append(norm_art)

            if not norm_artifacts:
                default_bytes = f"{rel_id}:{ver}".encode("utf-8")
                norm_artifacts.append({
                    "id": f"{rel_id}-config",
                    "type": "config",
                    "name": f"lyux-{pid}-{ver}.json",
                    "url": f"https://github.com/Luux-Manchot/lyux-desktop/releases/download/v{ver}/lyux-{pid}-{ver}.json",
                    "sha256": hashlib.sha256(default_bytes).hexdigest(),
                    "size": len(default_bytes),
                })

            manifest = self._build_default_manifest(pid, ver, norm_artifacts)
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
            rel = {
                "id": rel_id,
                "version": ver,
                "build": datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d"),
                "channel": channel,
                "family": family,
                "profile_id": pid,
                "state": "draft",
                "target": "Catalogue contrôlé",
                "author": actor,
                "notes": notes or "Brouillon déposé depuis le registre.",
                "released_at": now_iso,
                "published_at": None,
                "key_id": "",
                "signature": "En attente",
                "detached_signature": "",
                "manifest_hash": manifest_sha256(manifest),
                "manifest": manifest,
                "artifacts": norm_artifacts,
            }
            self._state.setdefault("releases", []).insert(0, rel)
            self._record_audit(actor, "create_draft", rel_id, f"Création brouillon {ver} ({pid})")
            self._atomic_save()
            return True, rel

    def sign_release(self, release_id: str, actor: str = "admin") -> Tuple[bool, Any]:
        with self._lock:
            rel = self.get_release(release_id)
            if not rel:
                return False, "Release introuvable."
            if rel["state"] in ("revoked", "removed"):
                return False, f"Impossible de signer une release au statut {rel['state']}."
            manifest = dict(rel["manifest"])
            manifest.pop("signature", None)
            sig, kid = self.key_manager.sign_manifest(manifest)
            manifest["signature"] = sig
            rel["manifest"] = manifest
            rel["detached_signature"] = sig
            rel["key_id"] = kid
            rel["signature"] = "Vérifiée"
            rel["manifest_hash"] = manifest_sha256(manifest)
            if rel["state"] == "draft":
                rel["state"] = "signed"
            self._record_audit(actor, "sign", release_id, f"Signature Ed25519 ({kid})")
            self._atomic_save()
            return True, rel

    def publish_release(self, release_id: str, actor: str = "admin") -> Tuple[bool, Any]:
        with self._lock:
            rel = self.get_release(release_id)
            if not rel:
                return False, "Release introuvable."
            if rel["state"] in ("revoked", "removed"):
                return False, f"Release {release_id} révoquée ou retirée."
            sig = rel.get("detached_signature", "")
            kid = rel.get("key_id", "")
            bundle = self.key_manager.get_public_bundle()
            pub_keys = {k["key_id"]: k["public_key_pem"] for k in bundle["keys"]}
            if not sig or kid not in pub_keys or not verify_ed25519_signature(rel["manifest"], sig, pub_keys[kid]):
                return False, "Publication refusée : signature Ed25519 absente ou invalide."
            rel["state"] = "published"
            rel["published_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
            self._record_audit(actor, "publish", release_id, f"Publication validée ({kid})")
            self._atomic_save()
            return True, rel

    def revoke_release(self, release_id: str, actor: str = "admin", reason: str = "") -> Tuple[bool, Any]:
        with self._lock:
            rel = self.get_release(release_id)
            if not rel:
                return False, "Release introuvable."
            rel["state"] = "revoked"
            rel["signature"] = "Révoquée"
            self._record_audit(actor, "revoke", release_id, reason or "Révocation administrative")
            self._atomic_save()
            return True, rel

    def rollback_to_release(self, release_id: str, actor: str = "admin") -> Tuple[bool, Any]:
        with self._lock:
            target = self.get_release(release_id)
            if not target:
                return False, "Release cible introuvable."
            if target["state"] in ("revoked", "removed"):
                return False, "Impossible de restaurer une release révoquée ou retirée."
            if not target.get("detached_signature"):
                return False, "Impossible de restaurer une release non signée."
            for r in self._state.get("releases", []):
                if r["id"] != release_id and r.get("profile_id") == target.get("profile_id") and r["state"] == "published":
                    r["state"] = "signed"
            target["state"] = "published"
            target["published_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
            self._record_audit(actor, "rollback", release_id, f"Restauration vers {target['version']}")
            self._atomic_save()
            return True, target

    def update_policy(self, policy_patch: Dict[str, Any], actor: str = "admin") -> Dict[str, Any]:
        with self._lock:
            self._state.setdefault("policy", {}).update(policy_patch)
            self._record_audit(actor, "update_policy", "policy", json.dumps(policy_patch, ensure_ascii=False))
            self._atomic_save()
            return dict(self._state["policy"])

    def build_client_manifest_response(
        self,
        *,
        building_id: str,
        room_id: str,
        role: str,
        profile_id: str,
        current_hash: str = "",
    ) -> Tuple[bool, Dict[str, Any]]:
        """Construit et signe le manifeste scopé pour un poste autorisé."""
        with self._lock:
            published = [
                r for r in self._state.get("releases", [])
                if r.get("state") == "published"
            ]
            if not published:
                return False, {"detail": "Aucun manifeste publié disponible."}

            selected = next((r for r in published if r.get("profile_id") == profile_id), published[0])
            rollback = next((r for r in published if r["id"] != selected["id"]), None)

            now = datetime.datetime.now(datetime.timezone.utc)
            scoped_manifest = {
                "schema": SCHEMA_NAME,
                "schema_version": SCHEMA_VERSION,
                "profile_id": profile_id if profile_id in STABLE_PROFILES else selected["profile_id"],
                "profile_version": selected["version"],
                "issued_at": (now - datetime.timedelta(seconds=5)).isoformat(timespec="seconds"),
                "expires_at": (now + datetime.timedelta(days=7)).isoformat(timespec="seconds"),
                "scope": {
                    "building_id": building_id,
                    "room_id": room_id,
                    "role": role,
                },
                "artifacts": list(selected["artifacts"]),
                "compatibility": {"debian": "13", "desktop": "plasma6-x11", "lyux_client_min": "1.0.0"},
            }
            sig, kid = self.key_manager.sign_manifest(scoped_manifest)
            scoped_manifest["signature"] = sig
            prof_hash = manifest_sha256(scoped_manifest)

            return True, {
                "manifest": scoped_manifest,
                "detached_signature": sig,
                "public_key_id": kid,
                "server_time": now.isoformat(timespec="seconds"),
                "not_modified": bool(current_hash and current_hash == selected.get("manifest_hash")),
                "profile_hash": prof_hash,
                "release_hash": selected.get("manifest_hash", prof_hash),
                "rollback_profile": rollback["profile_id"] if rollback else None,
            }
