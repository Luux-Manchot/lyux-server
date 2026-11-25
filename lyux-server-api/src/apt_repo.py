"""
Générateur et serveur de dépôt APT pilote signé pour LyuX (Debian 13 Trixie).
Construit des paquets .deb valides en pur Python (format ar + tar.gz),
génère Packages / Packages.gz / Release avec empreintes SHA-256 et signature Ed25519.
"""

import gzip
import hashlib
import io
import json
import os
import tarfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from profile_trust import Ed25519KeyManager


def _ar_member(name: str, data: bytes) -> bytes:
    header = (
        f"{name:<16}"
        f"{0:<12}"
        f"{0:<6}"
        f"{0:<6}"
        f"{'100644':<8}"
        f"{len(data):<10}"
        f"`\n"
    ).encode("ascii")
    body = data + (b"\n" if len(data) % 2 == 1 else b"")
    return header + body


def build_deb_package(
    *,
    package_name: str,
    version: str,
    architecture: str = "all",
    maintainer: str = "LyuX Team <contact@flowcrea.fr>",
    description: str = "LyuX pilot profile configuration package",
    files: Optional[Dict[str, bytes]] = None,
) -> bytes:
    """Construit un paquet Debian .deb binaire conforme au format ar (debian-binary + control + data)."""
    debian_binary = b"2.0\n"

    control_buf = io.BytesIO()
    control_txt = (
        f"Package: {package_name}\n"
        f"Version: {version}\n"
        f"Section: admin\n"
        f"Priority: optional\n"
        f"Architecture: {architecture}\n"
        f"Maintainer: {maintainer}\n"
        f"Description: {description}\n"
    ).encode("utf-8")
    with tarfile.open(fileobj=control_buf, mode="w:gz") as tf:
        ti = tarfile.TarInfo("./control")
        ti.size = len(control_txt)
        ti.mode = 0o644
        tf.addfile(ti, io.BytesIO(control_txt))

    data_buf = io.BytesIO()
    payload_files = files or {
        f"etc/lyux/profiles/{package_name}.json": json.dumps(
            {"package": package_name, "version": version}, indent=2
        ).encode("utf-8")
    }
    with tarfile.open(fileobj=data_buf, mode="w:gz") as tf:
        for rel_path, content in payload_files.items():
            clean = rel_path.lstrip("/")
            ti = tarfile.TarInfo(f"./{clean}")
            ti.size = len(content)
            ti.mode = 0o644
            tf.addfile(ti, io.BytesIO(content))

    return (
        b"!<arch>\n"
        + _ar_member("debian-binary", debian_binary)
        + _ar_member("control.tar.gz", control_buf.getvalue())
        + _ar_member("data.tar.gz", data_buf.getvalue())
    )


class SignedAptRepository:
    """Dépôt APT local limité aux paquets LyuX approuvés, avec Release signé Ed25519."""

    def __init__(self, repo_dir: Optional[Path] = None, key_manager: Optional[Ed25519KeyManager] = None):
        default_dir = os.getenv(
            "LYUX_APT_REPO_DIR",
            str(Path(__file__).resolve().parent.parent / "data" / "apt-repo"),
        )
        self.repo_dir = Path(repo_dir or default_dir)
        self.key_manager = key_manager or Ed25519KeyManager()
        self.suite = "trixie"
        self.component = "main"
        self.arch = "amd64"
        self._ensure_pilot_repo()

    def _ensure_pilot_repo(self) -> None:
        pool_dir = self.repo_dir / "pool" / self.component
        dist_dir = self.repo_dir / "dists" / self.suite / self.component / f"binary-{self.arch}"
        pool_dir.mkdir(parents=True, exist_ok=True)
        dist_dir.mkdir(parents=True, exist_ok=True)

        pilot_deb = pool_dir / "lyux-profile-standard_1.0.0_all.deb"
        if not pilot_deb.exists():
            deb_bytes = build_deb_package(
                package_name="lyux-profile-standard",
                version="1.0.0",
                description="Profil standard LyuX (socle KDE/X11 et Kiosk de base)",
                files={
                    "etc/lyux/profiles/standard.json": json.dumps(
                        {
                            "profile_id": "standard",
                            "version": "1.0.0",
                            "display_server": "x11",
                            "kiosk_base": True,
                        },
                        indent=2,
                    ).encode("utf-8")
                },
            )
            pilot_deb.write_bytes(deb_bytes)

        self.rebuild_index()

    def publish_deb(self, filename: str, deb_bytes: bytes) -> Dict[str, Any]:
        safe_name = os.path.basename(filename)
        if not safe_name.endswith(".deb"):
            raise ValueError("Seuls les paquets .deb sont acceptés.")
        pool_dir = self.repo_dir / "pool" / self.component
        pool_dir.mkdir(parents=True, exist_ok=True)
        dest = pool_dir / safe_name
        tmp = dest.with_suffix(".deb.tmp")
        tmp.write_bytes(deb_bytes)
        os.replace(tmp, dest)
        self.rebuild_index()
        return {
            "filename": safe_name,
            "sha256": hashlib.sha256(deb_bytes).hexdigest(),
            "size": len(deb_bytes),
        }

    def rebuild_index(self) -> Dict[str, Any]:
        pool_dir = self.repo_dir / "pool" / self.component
        dist_root = self.repo_dir / "dists" / self.suite
        bin_dir = dist_root / self.component / f"binary-{self.arch}"
        bin_dir.mkdir(parents=True, exist_ok=True)

        stanzas: List[str] = []
        for deb in sorted(pool_dir.glob("*.deb")):
            raw = deb.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            parts = deb.stem.split("_")
            pkg_name = parts[0]
            pkg_ver = parts[1] if len(parts) > 1 else "1.0.0"
            pkg_arch = parts[2] if len(parts) > 2 else "all"
            stanzas.append(
                f"Package: {pkg_name}\n"
                f"Version: {pkg_ver}\n"
                f"Architecture: {pkg_arch}\n"
                f"Filename: pool/{self.component}/{deb.name}\n"
                f"Size: {len(raw)}\n"
                f"SHA256: {sha}\n"
                f"Description: LyuX signed pilot package {pkg_name}\n"
            )

        packages_txt = "\n".join(stanzas).encode("utf-8")
        packages_gz = gzip.compress(packages_txt)
        (bin_dir / "Packages").write_bytes(packages_txt)
        (bin_dir / "Packages.gz").write_bytes(packages_gz)

        p_sha = hashlib.sha256(packages_txt).hexdigest()
        pgz_sha = hashlib.sha256(packages_gz).hexdigest()
        release_txt = (
            f"Origin: LyuX\n"
            f"Label: LyuX Pilot APT\n"
            f"Suite: {self.suite}\n"
            f"Codename: {self.suite}\n"
            f"Architectures: {self.arch} all\n"
            f"Components: {self.component}\n"
            f"SHA256:\n"
            f" {p_sha} {len(packages_txt)} {self.component}/binary-{self.arch}/Packages\n"
            f" {pgz_sha} {len(packages_gz)} {self.component}/binary-{self.arch}/Packages.gz\n"
        )
        (dist_root / "Release").write_text(release_txt, encoding="utf-8")

        sig, kid = self.key_manager.sign_manifest({"release": release_txt})
        (dist_root / "Release.ed25519").write_text(json.dumps({"key_id": kid, "signature": sig, "sha256": hashlib.sha256(release_txt.encode("utf-8")).hexdigest()}, indent=2), encoding="utf-8")
        return {"suite": self.suite, "packages_count": len(stanzas), "key_id": kid}

    def render_deb822_sources(self, base_url: str, keyring_path: str = "/etc/apt/keyrings/lyux-archive.gpg") -> str:
        return (
            f"Types: deb\n"
            f"URIs: {base_url.rstrip('/')}/api/v1/apt-repo\n"
            f"Suites: {self.suite}\n"
            f"Components: {self.component}\n"
            f"Signed-By: {keyring_path}\n"
        )
