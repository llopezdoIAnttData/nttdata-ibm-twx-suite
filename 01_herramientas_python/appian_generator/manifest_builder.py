"""
manifest_builder.py — Appian MANIFEST.MF + applicationHaul XML generator

Based on real Appian v26.3 ZIP structure:

META-INF/MANIFEST.MF:
    Manifest-Version: 1.0
    Appian-Version: 26.3.165.0
    Created-On: 2026-05-19T22:52:46.120Z

application/<uuid>.xml:
    <applicationHaul xmlns:a="http://www.appian.com/ae/types/2009">
        <versionUuid>...</versionUuid>
        <application>
            <name>NCI Redención Bono</name>
            <uuid>56e0108f-07e1-444d-9ad5-66aebade1aa4</uuid>
            <prefix>NCI_RB</prefix>
            <associatedObjects>
                <globalIdMap>
                    <item><type>content</type><uuids><uuid>...</uuid>...</uuids></item>
                    <item><type>processModel</type><uuids>...</uuids></item>
                    <item><type>recordType</type><uuids>...</uuids></item>
                    <item><type>group</type><uuids>...</uuids></item>
                </globalIdMap>
            </associatedObjects>
        </application>
    </applicationHaul>
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from .uuid_registry import UUIDRegistry

APPIAN_NS = "http://www.appian.com/ae/types/2009"


@dataclass
class AppianPackageManifest:
    """Tracks all objects added to the package for manifest generation."""
    app_name: str
    app_uuid: str
    app_prefix: str
    appian_version: str = "26.3.165.0"

    # Object UUIDs by type
    content_uuids: list = field(default_factory=list)
    process_model_uuids: list = field(default_factory=list)
    record_type_uuids: list = field(default_factory=list)
    group_uuids: list = field(default_factory=list)
    process_model_folder_uuids: list = field(default_factory=list)

    def add_content(self, uuid_str: str):
        if uuid_str not in self.content_uuids:
            self.content_uuids.append(uuid_str)

    def add_process_model(self, uuid_str: str):
        if uuid_str not in self.process_model_uuids:
            self.process_model_uuids.append(uuid_str)

    def add_record_type(self, uuid_str: str):
        if uuid_str not in self.record_type_uuids:
            self.record_type_uuids.append(uuid_str)

    def add_group(self, uuid_str: str):
        if uuid_str not in self.group_uuids:
            self.group_uuids.append(uuid_str)

    def total_objects(self) -> int:
        return (len(self.content_uuids) + len(self.process_model_uuids) +
                len(self.record_type_uuids) + len(self.group_uuids))


class ManifestBuilder:
    """
    Builds MANIFEST.MF and application XML for an Appian package.

    Usage:
        registry = UUIDRegistry()
        builder = ManifestBuilder(registry)
        manifest = builder.create_manifest(
            app_name="NCI Redención Bono",
            app_prefix="NCI_RB"
        )
        # ... add objects to manifest as they're created ...
        manifest.add_content(constant_uuid)

        mf_content = builder.build_manifest_mf(manifest)
        app_xml = builder.build_application_xml(manifest)
    """

    def __init__(self, registry: UUIDRegistry):
        self.registry = registry

    def create_manifest(self, app_name: str, app_prefix: str,
                         appian_version: str = "26.3.165.0") -> AppianPackageManifest:
        """Create a new manifest for an Appian package."""
        app_uuid = self.registry.get_or_create(f"APP:{app_name}")
        return AppianPackageManifest(
            app_name=app_name,
            app_uuid=app_uuid,
            app_prefix=app_prefix,
            appian_version=appian_version,
        )

    def build_manifest_mf(self, manifest: AppianPackageManifest,
                            export_time: Optional[datetime] = None) -> str:
        """Generate the META-INF/MANIFEST.MF content."""
        if export_time is None:
            export_time = datetime.now(timezone.utc)
        ts = export_time.strftime("%Y-%m-%dT%H:%M:%S.") + f"{export_time.microsecond // 1000:03d}Z"
        return (f"Manifest-Version: 1.0\n"
                f"Appian-Version: {manifest.appian_version}\n"
                f"Created-On: {ts}\n\n")

    def build_application_xml(self, manifest: AppianPackageManifest) -> str:
        """Generate the application/<uuid>.xml content."""
        version_uuid = self.registry.get_or_create(f"APP_VERSION:{manifest.app_name}")

        def uuids_block(uuids: list) -> str:
            if not uuids:
                return "<uuids/>"
            items = "\n".join(f"                    <uuid>{u}</uuid>" for u in uuids)
            return f"<uuids>\n{items}\n                </uuids>"

        content_block = uuids_block(manifest.content_uuids)
        pm_block = uuids_block(manifest.process_model_uuids)
        rt_block = uuids_block(manifest.record_type_uuids)
        grp_block = uuids_block(manifest.group_uuids)
        pmf_block = uuids_block(manifest.process_model_folder_uuids)

        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<applicationHaul xmlns:a="{APPIAN_NS}">
    <versionUuid>{version_uuid}</versionUuid>
    <application>
        <name>{manifest.app_name}</name>
        <uuid>{manifest.app_uuid}</uuid>
        <description></description>
        <parentUuid>SYSTEM_APPLICATIONS_ROOT</parentUuid>
        <visibility>
            <advertise>false</advertise>
            <hierarchy>true</hierarchy>
            <indexable>true</indexable>
            <quota>false</quota>
            <searchable>true</searchable>
            <system>false</system>
            <unlogged>false</unlogged>
        </visibility>
        <urlIdentifier>{manifest.app_prefix.lower().replace('_', '-')}</urlIdentifier>
        <published>false</published>
        <public>false</public>
        <prefix>{manifest.app_prefix}</prefix>
        <associatedObjects>
            <globalIdMap>
                <item>
                    <type>datatype</type>
                    <uuids/>
                </item>
                <item>
                    <type>dataStore</type>
                    <uuids/>
                </item>
                <item>
                    <type>user</type>
                    <uuids/>
                </item>
                <item>
                    <type>groupType</type>
                    <uuids/>
                </item>
                <item>
                    <type>group</type>
                    {grp_block}
                </item>
                <item>
                    <type>content</type>
                    {content_block}
                </item>
                <item>
                    <type>processModel</type>
                    {pm_block}
                </item>
                <item>
                    <type>processModelFolder</type>
                    {pmf_block}
                </item>
                <item>
                    <type>recordType</type>
                    {rt_block}
                </item>
            </globalIdMap>
        </associatedObjects>
    </application>
</applicationHaul>"""
