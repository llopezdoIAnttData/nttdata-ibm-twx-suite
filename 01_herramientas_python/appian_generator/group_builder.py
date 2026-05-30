"""
group_builder.py — Appian Security Group XML generator

Based on real Appian v26.3 group structure from NCI Redención Bono package.

Real structure in group/<uuid>.xml:
    <groupHaul xmlns:a="http://www.appian.com/ae/types/2009">
        <versionUuid>...</versionUuid>
        <group>
            <name>NCI_RB Administrators</name>
            <securityMap>SECURITYMAP_TEAM</securityMap>
            <uuid>...</uuid>
            <groupTypeUuid>SYSTEM_GROUP_TYPE_CUSTOM</groupTypeUuid>
            <description>...</description>
            <delegatedCreation>false</delegatedCreation>
            <memberPolicy>MEMBERPOLICY_CLOSED</memberPolicy>
            <viewingPolicy>VIEWINGPOLICY_LOW</viewingPolicy>
            <attributes/>
        </group>
        <members><users/><groups/></members>
        <admins>
            <users/>
            <groups><groupUuid>{self_uuid}</groupUuid></groups>
        </admins>
        <ruleSet/>
        <history>
            <historyInfo versionUuid="{uuid}"/>
        </history>
    </groupHaul>

IBM → Appian mapping:
  Per IBM BPM application → 2 standard Appian groups:
    {PREFIX} Administrators → Full access (ADMIN_OWNER in all role maps)
    {PREFIX} Users          → Basic access (VIEWER in role maps)
"""

from dataclasses import dataclass
from .uuid_registry import UUIDRegistry

APPIAN_NS = "http://www.appian.com/ae/types/2009"


@dataclass
class AppianGroup:
    """An Appian security group."""
    name: str
    uuid: str
    description: str = ""
    version_uuid: str = ""
    member_policy: str = "MEMBERPOLICY_CLOSED"
    viewing_policy: str = "VIEWINGPOLICY_LOW"

    def __post_init__(self):
        if not self.version_uuid:
            self.version_uuid = self.uuid


class GroupBuilder:
    """
    Builds Appian Security Group XML.

    For each IBM BPM application, generates the standard set of
    Appian groups needed for access control.

    Usage:
        builder = GroupBuilder(registry, app_prefix="NCI_RB")
        groups = builder.create_standard_groups()
        for group in groups:
            xml = builder.to_xml(group)
    """

    def __init__(self, registry: UUIDRegistry, app_prefix: str = "",
                 app_name: str = ""):
        self.registry = registry
        self.app_prefix = app_prefix
        self.app_name = app_name

    def create_standard_groups(self) -> list:
        """
        Create the standard Appian groups for a migrated IBM BPM application.

        Returns list of [admins_group, users_group].
        """
        prefix = self.app_prefix if self.app_prefix else self.app_name

        admin_uuid = self.registry.get_or_create(f"GROUP:ADMIN:{self.app_prefix}")
        users_uuid = self.registry.get_or_create(f"GROUP:USERS:{self.app_prefix}")

        return [
            AppianGroup(
                name=f"{prefix} Administrators",
                uuid=admin_uuid,
                description=f"Administrators group for {self.app_name or self.app_prefix}. "
                            f"Grants full access to all application objects.",
            ),
            AppianGroup(
                name=f"{prefix} Users",
                uuid=users_uuid,
                description=f"Users group for {self.app_name or self.app_prefix}. "
                            f"Grants standard access to application objects.",
                member_policy="MEMBERPOLICY_OPEN",
                viewing_policy="VIEWINGPOLICY_MEDIUM",
            ),
        ]

    def get_admin_group_uuid(self) -> str:
        """Return the UUID of the Administrators group (for role maps)."""
        return self.registry.get_or_create(f"GROUP:ADMIN:{self.app_prefix}")

    def get_users_group_uuid(self) -> str:
        """Return the UUID of the Users group."""
        return self.registry.get_or_create(f"GROUP:USERS:{self.app_prefix}")

    def to_xml(self, group: AppianGroup) -> str:
        """Serialize an AppianGroup to groupHaul XML."""
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<groupHaul xmlns:a="{APPIAN_NS}">
    <versionUuid>{group.uuid}</versionUuid>
    <group>
        <name>{self._esc(group.name)}</name>
        <securityMap>SECURITYMAP_TEAM</securityMap>
        <uuid>{group.uuid}</uuid>
        <groupTypeUuid>SYSTEM_GROUP_TYPE_CUSTOM</groupTypeUuid>
        <description>{self._esc(group.description)}</description>
        <delegatedCreation>false</delegatedCreation>
        <memberPolicy>{group.member_policy}</memberPolicy>
        <viewingPolicy>{group.viewing_policy}</viewingPolicy>
        <attributes/>
    </group>
    <members>
        <users/>
        <groups/>
    </members>
    <admins>
        <users/>
        <groups>
            <groupUuid>{group.uuid}</groupUuid>
        </groups>
    </admins>
    <ruleSet/>
    <history>
        <historyInfo versionUuid="{group.version_uuid}"/>
    </history>
</groupHaul>"""

    @staticmethod
    def _esc(text: str) -> str:
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
