"""TWX file parser — extracts and classifies all XML artifacts inside a .twx package.

IBM BPM TWX structure:
  META-INF/MANIFEST.MF  — basic manifest
  objects/{prefix}.{guid}.xml — all artifacts, classified by numeric prefix:

  Prefix → root element → artifact_type
  1      → <process>   → service_hhs / service_is / service_gss  (by processType 3/4/6)
  4      → <uca>       → uca
  7      → <webService>→ web_service
  12     → <twClass>   → business_object
  21     → <epv>       → exposed_process_variable
  24     → <participant>→ participant
  25     → <bpd>       → business_process
  61     → <managedAsset>→ managed_asset
  62     → <environmentVariableSet> → environment_variables
  63     → <projectDefaults> → project_defaults
  64     → <coachView> → coach_view
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import re


# Prefix → artifact_type (for prefixes with a single type)
PREFIX_TYPE_MAP = {
    "4":  "uca",
    "7":  "web_service",
    "12": "business_object",
    "21": "exposed_process_variable",
    "24": "participant",
    "25": "business_process",
    "61": "managed_asset",
    "62": "environment_variables",
    "63": "project_defaults",
    "64": "coach_view",
}

# processType values for prefix 1.* (services)
PROCESS_TYPE_MAP = {
    "3": "service_hhs",   # Human Service — pantallas de usuario
    "4": "service_is",    # Integration Service — llamadas a IIB/WS
    "6": "service_gss",   # General System Service — automáticos
}


@dataclass
class TWXArtifact:
    path: str
    artifact_type: str
    name: str
    prefix: str = ""
    raw_xml: Optional[str] = None
    tree: Optional[ET.ElementTree] = None
    guid: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    tags: list = field(default_factory=list)


@dataclass
class TWXPackage:
    file_path: str
    app_name: str = ""
    app_guid: str = ""
    app_version: str = ""
    app_acronym: str = ""
    toolkit: bool = False
    artifacts: list[TWXArtifact] = field(default_factory=list)
    manifest: dict = field(default_factory=dict)

    def by_type(self, artifact_type: str) -> list[TWXArtifact]:
        return [a for a in self.artifacts if a.artifact_type == artifact_type]

    def by_prefix(self, prefix: str) -> list[TWXArtifact]:
        return [a for a in self.artifacts if a.prefix == prefix]

    @property
    def summary(self) -> dict:
        counts: dict = {}
        for a in self.artifacts:
            counts[a.artifact_type] = counts.get(a.artifact_type, 0) + 1
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "toolkit": self.toolkit,
            "total_artifacts": len(self.artifacts),
            "by_type": counts,
        }


class TWXParser:
    """Opens a .twx file and returns a fully parsed TWXPackage."""

    def __init__(self, twx_path: str):
        self.twx_path = Path(twx_path)
        if not self.twx_path.exists():
            raise FileNotFoundError(f"TWX file not found: {twx_path}")
        if not zipfile.is_zipfile(self.twx_path):
            raise ValueError(f"File is not a valid TWX (ZIP) archive: {twx_path}")

    def parse(self) -> TWXPackage:
        package = TWXPackage(file_path=str(self.twx_path))

        with zipfile.ZipFile(self.twx_path, "r") as zf:
            entries = zf.namelist()
            self._parse_manifest(zf, entries, package)

            for entry in entries:
                if entry.startswith("__MACOSX") or entry.endswith("/"):
                    continue
                if not entry.startswith("objects/") or not entry.endswith(".xml"):
                    continue

                filename = Path(entry).name
                prefix = filename.split(".")[0]

                raw = zf.read(entry).decode("utf-8", errors="replace")

                # Determine artifact type
                artifact_type = self._classify(prefix, raw)
                if not artifact_type:
                    continue

                artifact = TWXArtifact(
                    path=entry,
                    artifact_type=artifact_type,
                    name=self._extract_name(raw),
                    prefix=prefix,
                    raw_xml=raw,
                )
                try:
                    artifact.tree = ET.ElementTree(ET.fromstring(raw))
                    root = artifact.tree.getroot()
                    # The actual artifact element is inside <teamworks>
                    child = next(iter(root), None)
                    if child is not None:
                        artifact.guid        = child.get("id", "")
                        artifact.version     = child.get("version") or child.get("snapshotVersion")
                        artifact.description = self._find_text(root, "description") or \
                                               self._find_text(root, "Documentation")
                        artifact.tags        = self._find_tags(root)
                except ET.ParseError:
                    pass

                package.artifacts.append(artifact)

            # Get app metadata from projectDefaults (63.*) if available
            if not package.app_name:
                self._extract_app_metadata(package)

        # Fallback: use filename as app name
        if not package.app_name:
            package.app_name = self.twx_path.stem

        return package

    # ── classification ────────────────────────────────────────────────────────

    def _classify(self, prefix: str, raw: str) -> Optional[str]:
        """Return artifact_type for a given prefix and raw XML content."""
        if prefix == "1":
            # Services: classify by processType
            pt = re.search(r"<processType>(\d+)</processType>", raw)
            if pt:
                return PROCESS_TYPE_MAP.get(pt.group(1), "service_other")
            return "service_other"
        return PREFIX_TYPE_MAP.get(prefix)

    # ── metadata helpers ──────────────────────────────────────────────────────

    def _parse_manifest(self, zf: zipfile.ZipFile, entries: list, package: TWXPackage) -> None:
        for candidate in entries:
            if candidate.endswith("MANIFEST.MF") or candidate.endswith("manifest.xml"):
                raw = zf.read(candidate).decode("utf-8", errors="replace")
                package.manifest["raw"] = raw

                # Standard BPM manifest fields
                for pattern, attr in [
                    (r"Process-App-Name:\s*(.+)",    "app_name"),
                    (r"Process-App-ID:\s*(.+)",      "app_guid"),
                    (r"Snapshot-Name:\s*(.+)",       "app_version"),
                    (r"Process-App-Acronym:\s*(.+)", "app_acronym"),
                ]:
                    m = re.search(pattern, raw)
                    if m:
                        setattr(package, attr, m.group(1).strip())

                tk_m = re.search(r"Is-Toolkit:\s*(.+)", raw)
                if tk_m:
                    package.toolkit = tk_m.group(1).strip().lower() == "true"
                return

    def _extract_app_metadata(self, package: TWXPackage) -> None:
        """Try to get app name from main BPD (25.*) — more reliable than projectDefaults."""
        # Prefer first business_process (BPD) name as the app name
        bpds = [a for a in package.artifacts if a.artifact_type == "business_process"]
        if bpds and bpds[0].name:
            package.app_name = bpds[0].name

        # Get version from project_defaults if available
        for artifact in package.artifacts:
            if artifact.artifact_type == "project_defaults" and artifact.tree:
                root = artifact.tree.getroot()
                child = next(iter(root), None)
                if child is not None:
                    ver = child.get("version") or child.get("snapshotVersion", "")
                    if ver:
                        package.app_version = ver
                break

    def _extract_name(self, raw: str) -> str:
        # Look for name attribute in the artifact element (second XML element)
        m = re.search(r"<\w+\s[^>]*\bname=['\"]([^'\"]+)['\"]", raw[:800])
        if m:
            return m.group(1)
        return ""

    def _find_text(self, root: ET.Element, tag: str) -> Optional[str]:
        for el in root.iter():
            if el.tag.split("}")[-1] == tag and el.text:
                return el.text.strip()
        return None

    def _find_tags(self, root: ET.Element) -> list:
        tags = []
        for el in root.iter():
            if el.tag.split("}")[-1] in ("tag", "Tag", "keyword"):
                if el.text:
                    tags.append(el.text.strip())
        return tags

