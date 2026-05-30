"""
constants_builder.py — IBM BPM Variables/Constants → Appian <constant> XML

Based on real Appian v26.3 ZIP analysis of NCI Redención Bono package.

Real constant structure inside content/<uuid>.xml:
    <contentHaul xmlns:a="http://www.appian.com/ae/types/2009">
        <versionUuid>...</versionUuid>
        <constant>
            <name>NCI_RB_TXT_SNAPSHOT</name>
            <uuid>...</uuid>
            <description>...</description>
            <parentUuid>...</parentUuid>
            <visibility>...</visibility>
            <typedValue>
                <type>
                    <name>string</name>
                    <namespace>http://www.w3.org/2001/XMLSchema</namespace>
                </type>
                <value>Profuturo Redencion Bono V 1.0</value>
            </typedValue>
            <isEnvironmentSpecific>false</isEnvironmentSpecific>
        </constant>
        <roleMap public="true">...</roleMap>
        <history>...</history>
    </contentHaul>

IBM → Appian type mapping:
    IBM String   → string     (ns: http://www.w3.org/2001/XMLSchema)
    IBM Integer  → int        (ns: http://www.w3.org/2001/XMLSchema)
    IBM Decimal  → decimal    (ns: http://www.w3.org/2001/XMLSchema)
    IBM Boolean  → boolean    (ns: http://www.w3.org/2001/XMLSchema)
    IBM Date     → date       (ns: http://www.w3.org/2001/XMLSchema)
    IBM DateTime → dateTime   (ns: http://www.w3.org/2001/XMLSchema)
    IBM List     → type?list  (ns: http://www.appian.com/ae/types/2009)
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from .uuid_registry import UUIDRegistry

# Namespace constants
XSD_NS = "http://www.w3.org/2001/XMLSchema"
APPIAN_NS = "http://www.appian.com/ae/types/2009"

# IBM type → Appian type mapping
IBM_TO_APPIAN_TYPE = {
    # Primitives
    "String":   ("string",  XSD_NS),
    "String[]": ("Text?list", APPIAN_NS),
    "Integer":  ("int",     XSD_NS),
    "Integer[]": ("Integer?list", APPIAN_NS),
    "Decimal":  ("decimal", XSD_NS),
    "Boolean":  ("boolean", XSD_NS),
    "Date":     ("date",    XSD_NS),
    "DateTime": ("dateTime", XSD_NS),
    # Appian native
    "Text":     ("string",  XSD_NS),
    "Text[]":   ("Text?list", APPIAN_NS),
    "Number (Decimal)": ("decimal", XSD_NS),
    "Number (Integer)": ("int", XSD_NS),
}

ROLE_MAP_TEMPLATE = """    <roleMap public="true">
        <role inherit="true" allowForAll="false" name="readers"><users/><groups/></role>
        <role inherit="true" allowForAll="false" name="authors"><users/><groups/></role>
        <role inherit="true" allowForAll="false" name="administrators"><users/><groups/></role>
        <role inherit="false" allowForAll="false" name="denyReaders"><users/><groups/></role>
        <role inherit="false" allowForAll="false" name="denyAuthors"><users/><groups/></role>
        <role inherit="false" allowForAll="false" name="denyAdministrators"><users/><groups/></role>
    </roleMap>"""


@dataclass
class AppianConstant:
    """Represents an Appian constant ready to be serialized to XML."""
    name: str                           # e.g. "NCI_RB_TXT_SNAPSHOT"
    uuid: str                           # UUID string
    description: str = ""
    parent_uuid: str = ""               # UUID of parent folder
    ibm_type: str = "String"            # IBM type key
    value: Any = ""                     # The constant value
    is_env_specific: bool = False       # true for URLs, credentials, etc.
    version_uuid: str = ""              # versionUuid (same as uuid if new)

    def __post_init__(self):
        if not self.version_uuid:
            self.version_uuid = self.uuid


@dataclass
class AppianRulesFolder:
    """Represents a folder to group constants/rules in Appian."""
    name: str                           # e.g. "NCI_RB Constants"
    uuid: str
    description: str = ""
    parent_uuid: str = ""
    version_uuid: str = ""

    def __post_init__(self):
        if not self.version_uuid:
            self.version_uuid = self.uuid


class ConstantsBuilder:
    """
    Builds Appian constant XML files from IBM BPM variable/constant data.

    Usage:
        registry = UUIDRegistry()
        builder = ConstantsBuilder(registry, app_prefix="NCI_RB")

        # From IBM variable
        constant = builder.from_ibm_variable(
            name="MAX_MONTO",
            ibm_type="Decimal",
            value="999999.99",
            description="Monto máximo de redención"
        )
        xml = builder.to_xml(constant)
    """

    def __init__(self, registry: UUIDRegistry, app_prefix: str = "NCI_RB",
                 default_parent_uuid: str = ""):
        self.registry = registry
        self.app_prefix = app_prefix
        self.default_parent_uuid = default_parent_uuid

    def from_ibm_variable(self, name: str, ibm_type: str = "String",
                           value: Any = "", description: str = "",
                           parent_uuid: str = "", is_env_specific: bool = False) -> AppianConstant:
        """
        Create an AppianConstant from an IBM BPM variable/constant.

        Args:
            name: Variable name (prefix will be added if not present)
            ibm_type: IBM data type (String, Integer, Decimal, Boolean, etc.)
            value: The constant value
            description: Optional description
            parent_uuid: UUID of parent folder in Appian
            is_env_specific: Mark as environment-specific (for URLs, etc.)
        """
        # Normalize name with prefix
        appian_name = self._normalize_name(name)
        uuid_str = self.registry.get_or_create(f"CONST:{appian_name}")

        return AppianConstant(
            name=appian_name,
            uuid=uuid_str,
            description=description,
            parent_uuid=parent_uuid or self.default_parent_uuid,
            ibm_type=ibm_type,
            value=value,
            is_env_specific=is_env_specific,
        )

    def create_folder(self, folder_name: str, description: str = "",
                       parent_uuid: str = "") -> AppianRulesFolder:
        """Create a rules folder (to group constants)."""
        uuid_str = self.registry.get_or_create(f"FOLDER:{folder_name}")
        return AppianRulesFolder(
            name=folder_name,
            uuid=uuid_str,
            description=description,
            parent_uuid=parent_uuid,
        )

    def to_xml(self, obj: "AppianConstant | AppianRulesFolder") -> str:
        """Serialize an AppianConstant or AppianRulesFolder to XML string."""
        if isinstance(obj, AppianRulesFolder):
            return self._folder_to_xml(obj)
        return self._constant_to_xml(obj)

    def _constant_to_xml(self, c: AppianConstant) -> str:
        type_name, type_ns = IBM_TO_APPIAN_TYPE.get(c.ibm_type, ("string", XSD_NS))
        value_xml = self._escape_xml(str(c.value)) if c.value is not None else ""
        parent_xml = f"<parentUuid>{c.parent_uuid}</parentUuid>" if c.parent_uuid else ""
        env_specific = "true" if c.is_env_specific else "false"

        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<contentHaul xmlns:a="{APPIAN_NS}">
    <versionUuid>{c.version_uuid}</versionUuid>
    <constant>
        <name>{self._escape_xml(c.name)}</name>
        <uuid>{c.uuid}</uuid>
        <description>{self._escape_xml(c.description)}</description>
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
        <typedValue>
            <type>
                <name>{type_name}</name>
                <namespace>{type_ns}</namespace>
            </type>
            <value>{value_xml}</value>
        </typedValue>
        <isEnvironmentSpecific>{env_specific}</isEnvironmentSpecific>
    </constant>
{ROLE_MAP_TEMPLATE}
    <history>
        <historyInfo versionUuid="{c.version_uuid}"/>
    </history>
</contentHaul>"""

    def _folder_to_xml(self, f: AppianRulesFolder) -> str:
        parent_xml = f"<parentUuid>{f.parent_uuid}</parentUuid>" if f.parent_uuid else ""
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<contentHaul xmlns:a="{APPIAN_NS}">
    <versionUuid>{f.version_uuid}</versionUuid>
    <rulesFolder>
        <name>{self._escape_xml(f.name)}</name>
        <uuid>{f.uuid}</uuid>
        <description>{self._escape_xml(f.description)}</description>
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
    </rulesFolder>
{ROLE_MAP_TEMPLATE}
    <history>
        <historyInfo versionUuid="{f.version_uuid}"/>
    </history>
</contentHaul>"""

    def _normalize_name(self, name: str) -> str:
        """Add app prefix if not present."""
        prefix = f"{self.app_prefix}_"
        if not name.startswith(prefix):
            return f"{prefix}{name}"
        return name

    @staticmethod
    def _escape_xml(text: str) -> str:
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))
