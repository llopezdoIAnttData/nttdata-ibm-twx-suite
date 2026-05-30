"""
zip_packager.py — Assembles final Appian importable .zip from generated objects

Appian ZIP structure (real v26.3):
    app.zip/
    ├── META-INF/MANIFEST.MF
    ├── application/<app_uuid>.xml
    ├── content/<uuid>.xml          (constants, rules, interfaces, integrations)
    ├── processModel/<uuid>.xml
    ├── processModelFolder/<uuid>.xml
    ├── recordType/<uuid>.xml
    └── group/<uuid>.xml

Usage:
    packager = ZipPackager(manifest, manifest_builder)
    packager.add_content(constant_uuid, constant_xml)
    packager.add_content(folder_uuid, folder_xml)
    zip_path = packager.build("output/Profuturo-RedencionBono-v1.zip")
"""

import zipfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from .manifest_builder import ManifestBuilder, AppianPackageManifest


class ZipPackager:
    """
    Assembles all generated Appian XML objects into an importable .zip file.

    Each object type goes into a specific folder matching the Appian structure.
    """

    def __init__(self, manifest: AppianPackageManifest,
                 manifest_builder: ManifestBuilder):
        self.manifest = manifest
        self.manifest_builder = manifest_builder
        self._content: dict[str, str] = {}         # uuid → xml
        self._process_models: dict[str, str] = {}
        self._process_model_folders: dict[str, str] = {}
        self._record_types: dict[str, str] = {}
        self._groups: dict[str, str] = {}

    def add_content(self, uuid_str: str, xml: str):
        """Add a content object (constant, rule, interface, etc.)."""
        self._content[uuid_str] = xml
        self.manifest.add_content(uuid_str)

    def add_process_model(self, uuid_str: str, xml: str):
        """Add a process model."""
        self._process_models[uuid_str] = xml
        self.manifest.add_process_model(uuid_str)

    def add_process_model_folder(self, uuid_str: str, xml: str):
        """Add a process model folder."""
        self._process_model_folders[uuid_str] = xml
        self.manifest.process_model_folder_uuids.append(uuid_str)

    def add_record_type(self, uuid_str: str, xml: str):
        """Add a record type."""
        self._record_types[uuid_str] = xml
        self.manifest.add_record_type(uuid_str)

    def add_group(self, uuid_str: str, xml: str):
        """Add a security group."""
        self._groups[uuid_str] = xml
        self.manifest.add_group(uuid_str)

    def build(self, output_path: str, export_time: Optional[datetime] = None) -> Path:
        """
        Build the final .zip file.

        Args:
            output_path: Path for the output .zip file
            export_time: Timestamp to use in MANIFEST.MF

        Returns:
            Path to the generated ZIP file
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        if export_time is None:
            export_time = datetime.now(timezone.utc)

        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # META-INF/MANIFEST.MF
            mf_content = self.manifest_builder.build_manifest_mf(
                self.manifest, export_time
            )
            zf.writestr("META-INF/MANIFEST.MF", mf_content.encode("utf-8"))

            # application/<uuid>.xml — must be AFTER objects are added
            app_xml = self.manifest_builder.build_application_xml(self.manifest)
            zf.writestr(
                f"application/{self.manifest.app_uuid}.xml",
                app_xml.encode("utf-8")
            )

            # content/
            for uuid_str, xml in self._content.items():
                zf.writestr(f"content/{uuid_str}.xml", xml.encode("utf-8"))

            # processModel/
            for uuid_str, xml in self._process_models.items():
                zf.writestr(f"processModel/{uuid_str}.xml", xml.encode("utf-8"))

            # processModelFolder/
            for uuid_str, xml in self._process_model_folders.items():
                zf.writestr(f"processModelFolder/{uuid_str}.xml", xml.encode("utf-8"))

            # recordType/
            for uuid_str, xml in self._record_types.items():
                zf.writestr(f"recordType/{uuid_str}.xml", xml.encode("utf-8"))

            # group/
            for uuid_str, xml in self._groups.items():
                zf.writestr(f"group/{uuid_str}.xml", xml.encode("utf-8"))

        return output

    def summary(self) -> dict:
        """Return a summary of what's in the package."""
        return {
            "app_name": self.manifest.app_name,
            "app_prefix": self.manifest.app_prefix,
            "content_objects": len(self._content),
            "process_models": len(self._process_models),
            "record_types": len(self._record_types),
            "groups": len(self._groups),
            "total_objects": self.manifest.total_objects(),
        }
