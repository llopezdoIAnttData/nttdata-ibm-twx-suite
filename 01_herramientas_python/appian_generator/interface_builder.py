"""
interface_builder.py — IBM BPM Coach View → Appian Interface XML

Generates STUB Appian interfaces from IBM Coach View metadata.

The stub interface contains:
  - Correct name and description
  - A minimal definition with a TODO placeholder showing the IBM Coach View name
  - All the right metadata (uuid, parentUuid, visibility)

Appian Interface XML (inside content/<uuid>.xml):
    <contentHaul xmlns:a="http://www.appian.com/ae/types/2009">
        <versionUuid>...</versionUuid>
        <interface>
            <name>...</name>
            <uuid>...</uuid>
            <description>...</description>
            <parentUuid>...</parentUuid>
            <visibility>...</visibility>
            <definition>a!cardLayout(...)</definition>
        </interface>
        <roleMap>...</roleMap>
        <history>...</history>
    </contentHaul>

IBM Coach View → Appian Interface mapping:
  coachView name  → interface name (with prefix)
  coachView id    → used to derive UUID (via registry)
  layout XML      → NOT translated (too complex, just stub)
"""

from dataclasses import dataclass, field as dc_field
from .uuid_registry import UUIDRegistry

APPIAN_NS = "http://www.appian.com/ae/types/2009"

ROLE_MAP_TEMPLATE = """    <roleMap public="true">
        <role inherit="true" allowForAll="false" name="readers"><users/><groups/></role>
        <role inherit="true" allowForAll="false" name="authors"><users/><groups/></role>
        <role inherit="true" allowForAll="false" name="administrators"><users/><groups/></role>
        <role inherit="false" allowForAll="false" name="denyReaders"><users/><groups/></role>
        <role inherit="false" allowForAll="false" name="denyAuthors"><users/><groups/></role>
        <role inherit="false" allowForAll="false" name="denyAdministrators"><users/><groups/></role>
    </roleMap>"""


@dataclass
class AppianInterface:
    """An Appian Interface ready for serialization."""
    name: str
    uuid: str
    description: str = ""
    parent_uuid: str = ""
    definition: str = ""
    version_uuid: str = ""
    source_ibm_name: str = ""

    def __post_init__(self):
        if not self.version_uuid:
            self.version_uuid = self.uuid


class InterfaceBuilder:
    """
    Builds Appian Interface XML stubs from IBM Coach View metadata.

    Usage:
        builder = InterfaceBuilder(registry, app_prefix="NCI_RB",
                                   default_parent_uuid="...")
        iface = builder.from_ibm_coach_view(name, ibm_id, description)
        xml = builder.to_xml(iface)
    """

    def __init__(self, registry: UUIDRegistry, app_prefix: str = "",
                 default_parent_uuid: str = ""):
        self.registry = registry
        self.app_prefix = app_prefix
        self.default_parent_uuid = default_parent_uuid

    def from_ibm_coach_view(self, name: str, ibm_id: str = "",
                             description: str = "",
                             parent_uuid: str = "") -> AppianInterface:
        """Create an Appian Interface stub from an IBM Coach View."""
        prefix = f"{self.app_prefix}_" if self.app_prefix else ""
        clean = name.replace(" ", "_").replace("-", "_")
        appian_name = f"{prefix}{clean}" if not name.startswith(prefix) else name

        uuid_str = self.registry.get_or_create(f"IFACE:{appian_name}")

        definition = f"""a!localVariables(
  /* ============================================================
     TODO: Implement interface for IBM Coach View: {self._esc_el(name)}
     
     This is a generated stub. Replace with actual Appian
     interface components (a!formLayout, a!sectionLayout, etc.)
     
     IBM Coach View ID: {ibm_id}
     ============================================================ */
  a!cardLayout(
    contents: {{
      a!richTextDisplayField(
        labelPosition: "COLLAPSED",
        value: {{
          a!richTextItem(
            text: "TODO: Implement interface for {self._esc_el(name)}",
            style: "STRONG",
            size: "MEDIUM"
          )
        }}
      )
    }},
    showBorder: false
  )
)"""

        return AppianInterface(
            name=appian_name,
            uuid=uuid_str,
            description=description or f"Interface migrated from IBM Coach View: {name}",
            parent_uuid=parent_uuid or self.default_parent_uuid,
            definition=definition,
            source_ibm_name=name,
        )

    def to_xml(self, iface: AppianInterface) -> str:
        """Serialize an AppianInterface to contentHaul XML."""
        parent_xml = f"<parentUuid>{iface.parent_uuid}</parentUuid>" if iface.parent_uuid else ""
        definition_escaped = self._escape(iface.definition)

        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<contentHaul xmlns:a="{APPIAN_NS}">
    <versionUuid>{iface.version_uuid}</versionUuid>
    <interface>
        <name>{self._escape(iface.name)}</name>
        <uuid>{iface.uuid}</uuid>
        <description>{self._escape(iface.description)}</description>
        {parent_xml}
        <visibility>
            <advertise>false</advertise>
            <hierarchy>true</hierarchy>
            <indexable>true</indexable>
            <quota>false</quota>
            <searchable>true</searchable>
            <system>false</system>
            <unlogged>false</unlogged>
        </visibility>
        <definition>{definition_escaped}</definition>
    </interface>
{ROLE_MAP_TEMPLATE}
    <history>
        <historyInfo versionUuid="{iface.version_uuid}"/>
    </history>
</contentHaul>"""

    @staticmethod
    def _escape(text: str) -> str:
        return (str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))

    @staticmethod
    def _esc_el(text: str) -> str:
        """Escape for use inside Appian EL string literals."""
        return str(text).replace('"', '\\"').replace("\\", "\\\\")
