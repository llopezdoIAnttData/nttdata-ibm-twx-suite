"""
record_type_builder.py — IBM Business Object → Appian Record Type XML

Based on real Appian v26.3 recordType structure observed in NCI Redención Bono package.

The Appian Record Type (RDBMS_TABLE source) maps directly to a DB table.
IBM BOs become Record Types backed by database tables.

Real structure:
    <recordTypeHaul xmlns:a="..." xmlns:xsi="...">
        <versionUuid>UUID</versionUuid>
        <recordType a:uuid="UUID" name="NCI_RB EventType">
            <a:pluralName>NCI_RB EventTypes</a:pluralName>
            <a:description>...</a:description>
            <a:source xsi:type="a:RecordsReplica"/>
            <a:sourceConfiguration>
                <sourceUuid>Appian.TABLENAME@jdbc/Appian</sourceUuid>
                <sourceType>RDBMS_TABLE</sourceType>
                <field>
                    <uuid>UUID</uuid>
                    <type>{http://www.appian.com/ae/types/2009}Integer</type>
                    <sourceFieldName>COLUMN_NAME</sourceFieldName>
                    <sourceFieldType>INTEGER</sourceFieldType>
                    <fieldName>camelCaseName</fieldName>
                    <displayName>Display Name</displayName>
                    <isRecordId>true/false</isRecordId>
                    ...
                </field>
            </a:sourceConfiguration>
        </recordType>
        <roleMap>...</roleMap>
    </recordTypeHaul>
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from .uuid_registry import UUIDRegistry
from .ibm_twx_parser import IBMBusinessObject, IBMField, IBM_TYPE_MAP

APPIAN_NS = "http://www.appian.com/ae/types/2009"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

# IBM field type → (Appian type in braces, SQL column type)
APPIAN_TYPE_MAP = {
    "string":   ("{http://www.appian.com/ae/types/2009}Text",    "VARCHAR(255)"),
    "String":   ("{http://www.appian.com/ae/types/2009}Text",    "VARCHAR(255)"),
    "int":      ("{http://www.appian.com/ae/types/2009}Integer", "INTEGER"),
    "integer":  ("{http://www.appian.com/ae/types/2009}Integer", "INTEGER"),
    "Integer":  ("{http://www.appian.com/ae/types/2009}Integer", "INTEGER"),
    "long":     ("{http://www.appian.com/ae/types/2009}Integer", "BIGINT"),
    "decimal":  ("{http://www.appian.com/ae/types/2009}Decimal", "DECIMAL(18,2)"),
    "Decimal":  ("{http://www.appian.com/ae/types/2009}Decimal", "DECIMAL(18,2)"),
    "float":    ("{http://www.appian.com/ae/types/2009}Decimal", "DECIMAL(18,4)"),
    "double":   ("{http://www.appian.com/ae/types/2009}Decimal", "DECIMAL(18,4)"),
    "boolean":  ("{http://www.appian.com/ae/types/2009}Boolean", "TINYINT(1)"),
    "Boolean":  ("{http://www.appian.com/ae/types/2009}Boolean", "TINYINT(1)"),
    "date":     ("{http://www.appian.com/ae/types/2009}Date",    "DATE"),
    "dateTime": ("{http://www.appian.com/ae/types/2009}DateTime","DATETIME"),
    "Date":     ("{http://www.appian.com/ae/types/2009}Date",    "DATE"),
    "DateTime": ("{http://www.appian.com/ae/types/2009}DateTime","DATETIME"),
}

# Appian group role names for record type
DEFAULT_ADMIN_GROUP = ""  # Will be set from manifest
DEFAULT_VIEWER_GROUP = ""

ROLE_MAP_TEMPLATE = """    <roleMap>
        <role name="record_type_administrator">
            <users/>
            <groups>{admin_group}</groups>
        </role>
        <role name="record_type_data_steward">
            <users/>
            <groups/>
        </role>
        <role name="record_type_viewer">
            <users/>
            <groups>{viewer_group}</groups>
        </role>
    </roleMap>"""


def _to_snake_upper(name: str) -> str:
    """Convert camelCase or PascalCase to UPPER_SNAKE_CASE for column names."""
    s1 = re.sub(r'([A-Z])', r'_\1', name)
    return s1.upper().lstrip("_")


def _to_camel(name: str) -> str:
    """Convert UPPER_SNAKE_CASE or snake_case to camelCase."""
    parts = name.lower().split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _make_display_name(name: str) -> str:
    """Convert fieldName to human-readable Display Name."""
    s = re.sub(r'([A-Z])', r' \1', name).strip()
    return s.capitalize()


class RecordTypeBuilder:
    """
    Builds Appian Record Type XML from IBM Business Object definitions.

    Record Types in Appian (backed by RDBMS_TABLE) map 1:1 to IBM BOs.
    Each BO field becomes a Record Type field with a corresponding DB column.

    Usage:
        builder = RecordTypeBuilder(registry, app_prefix="NCI_RB")
        record_xml = builder.from_ibm_bo(ibm_bo, admin_group_uuid="...", viewer_group_uuid="...")
    """

    def __init__(self, registry: UUIDRegistry, app_prefix: str = "NCI_RB",
                 datasource: str = "jdbc/Appian"):
        self.registry = registry
        self.app_prefix = app_prefix
        self.datasource = datasource

    def from_ibm_bo(self, bo: IBMBusinessObject,
                     admin_group_uuid: str = "",
                     viewer_group_uuid: str = "",
                     table_prefix: str = "") -> tuple[str, str]:
        """
        Generate Appian Record Type XML from an IBM Business Object.

        Args:
            bo: IBM Business Object data
            admin_group_uuid: UUID of admin group in Appian
            viewer_group_uuid: UUID of viewer group in Appian
            table_prefix: Prefix for DB table name (e.g. "NCIRB_")

        Returns:
            Tuple of (record_type_uuid, xml_content)
        """
        # Generate names
        rt_name = f"{self.app_prefix} {bo.name}"
        rt_uuid = self.registry.get_or_create(f"RT:{bo.name}")
        version_uuid = self.registry.get_or_create(f"RT_VERSION:{bo.name}")

        # DB table name from BO name
        t_prefix = table_prefix or f"{self.app_prefix.replace('_', '')}_"
        table_name = f"{t_prefix}{_to_snake_upper(bo.name)}"
        # Truncate table name if too long
        if len(table_name) > 64:
            table_name = table_name[:64]

        source_uuid = f"Appian.{table_name}@{self.datasource}"

        # Generate field XMLs
        fields_xml = self._build_fields(bo, rt_uuid)

        # Group XMLs
        admin_grp_xml = f"<groupUuid>{admin_group_uuid}</groupUuid>" if admin_group_uuid else ""
        viewer_grp_xml = f"<groupUuid>{viewer_group_uuid}</groupUuid>" if viewer_group_uuid else ""

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<recordTypeHaul xmlns:a="{APPIAN_NS}" xmlns:xsi="{XSI_NS}">
  <versionUuid>{version_uuid}</versionUuid>
  <recordType a:uuid="{rt_uuid}" name="{self._escape(rt_name)}">
    <a:pluralName>{self._escape(rt_name)}s</a:pluralName>
    <a:description>{self._escape(bo.description or f'Record type for IBM BO: {bo.name}')}</a:description>
    <a:urlStub>{rt_uuid[:6]}</a:urlStub>
    <a:source xsi:type="a:RecordsReplica"/>
    <a:listViewTemplateExpr/>
    <a:detailViewCfg>
      <a:nameExpr>#"SYSTEM_SYSRULES_rtd_getDefaultSummaryViewName"()</a:nameExpr>
      <a:uiExpr/>
      <a:visibilityExpr>=true()</a:visibilityExpr>
      <a:urlStub>summary</a:urlStub>
      <a:headerExpr/>
      <a:recordActionLaunchType>DIALOG</a:recordActionLaunchType>
      <a:recordUiSecurityType>EXPRESSION</a:recordUiSecurityType>
    </a:detailViewCfg>
    <a:isSystem>false</a:isSystem>
    <a:dataSrcExpr/>
    <a:facetsListExpr/>
    <a:titleExpr/>
    <a:defaultFiltersExpr/>
    <a:layoutType>GRID</a:layoutType>
    <a:security>16383</a:security>
    <a:hideLatestNews>false</a:hideLatestNews>
    <a:hideNewsView>false</a:hideNewsView>
    <a:hideRelatedActionsView>false</a:hideRelatedActionsView>
    <a:isExportable>true</a:isExportable>
    <a:listViewSrcExpr/>
    <a:recordViewSrcExpr/>
    <a:recordTypeSearchCfg>
      <searchFieldsSrc>DEFAULT</searchFieldsSrc>
      <placeholderSrc>DEFAULT</placeholderSrc>
      <placeholder/>
    </a:recordTypeSearchCfg>
    <a:iconId/>
    <a:listAutoRefreshInterval>0.0</a:listAutoRefreshInterval>
    <a:sourceConfiguration>
      <sourceUuid>{source_uuid}</sourceUuid>
      <sourceType>RDBMS_TABLE</sourceType>
      <sourceSubType>NONE</sourceSubType>
      <sourceContextExpr/>
      <friendlyName>{table_name}</friendlyName>
      <sourceFilterExpr/>
{fields_xml}
      <uuid>{self.registry.get_or_create(f"RT_SRC:{bo.name}")}</uuid>
      <refreshSchedule>
        <value>{{"hour":3,"minute":"00","amPM":"AM","timeZone":"America/Mexico_City","version":"v1"}}</value>
        <activated>false</activated>
      </refreshSchedule>
      <skipFailureEnabled>true</skipFailureEnabled>
      <recordIdGeneratorUuid/>
    </a:sourceConfiguration>
    <a:enabledFeatures>2047</a:enabledFeatures>
    <a:isVisibleInRecordTypeList>true</a:isVisibleInRecordTypeList>
    <a:recordActionLaunchType>DIALOG</a:recordActionLaunchType>
    <a:showSearchBox>true</a:showSearchBox>
    <a:isVisibleInDataFabric>true</a:isVisibleInDataFabric>
    <a:usesRollingSyncLimit>false</a:usesRollingSyncLimit>
    <a:usesRecoverySync>false</a:usesRecoverySync>
    <a:isScheduledIndexingEnabled>false</a:isScheduledIndexingEnabled>
    <a:smartSearchAcceptableFailureRate>0.0</a:smartSearchAcceptableFailureRate>
    <a:skipFailedSmartServicesSync>false</a:skipFailedSmartServicesSync>
    <a:creationSource>UNKNOWN</a:creationSource>
    <a:sqlEnabled>false</a:sqlEnabled>
  </recordType>
  <roleMap>
    <role name="record_type_administrator">
      <users/>
      <groups>{admin_grp_xml}</groups>
    </role>
    <role name="record_type_data_steward">
      <users/>
      <groups/>
    </role>
    <role name="record_type_viewer">
      <users/>
      <groups>{viewer_grp_xml}</groups>
    </role>
  </roleMap>
  <history>
    <historyInfo versionUuid="{version_uuid}"/>
  </history>
  <migrationVersion>1</migrationVersion>
</recordTypeHaul>"""

        return rt_uuid, xml

    def _build_fields(self, bo: IBMBusinessObject, rt_uuid: str) -> str:
        """Build the field XML blocks for a Record Type."""
        if not bo.fields:
            # Add a default ID field
            return self._field_xml(
                field_uuid=self.registry.get_or_create(f"RT_FIELD:{bo.name}:id"),
                rt_uuid=rt_uuid,
                appian_type="{http://www.appian.com/ae/types/2009}Integer",
                source_field_name="ID",
                source_field_type="INTEGER",
                field_name="id",
                display_name="Id",
                is_record_id=True
            )

        lines = []
        has_id = any(f.name.lower() in ("id", "iid", "pk", "primarykey") for f in bo.fields)

        for i, f in enumerate(bo.fields):
            # Determine if this is the primary key
            is_pk = (not has_id and i == 0) or f.name.lower() in ("id", "iid")

            appian_type, sql_type = APPIAN_TYPE_MAP.get(
                f.type_name, ("{http://www.appian.com/ae/types/2009}Text", "VARCHAR(255)")
            )
            if f.is_custom_type:
                # Custom type → store as Text (JSON)
                appian_type = "{http://www.appian.com/ae/types/2009}Text"
                sql_type = "TEXT"

            col_name = _to_snake_upper(f.name)
            camel_name = f.name  # keep original camelCase

            lines.append(self._field_xml(
                field_uuid=self.registry.get_or_create(f"RT_FIELD:{bo.name}:{f.name}"),
                rt_uuid=rt_uuid,
                appian_type=appian_type,
                source_field_name=col_name,
                source_field_type=sql_type,
                field_name=camel_name,
                display_name=_make_display_name(f.name),
                is_record_id=is_pk,
            ))

        return "\n".join(lines)

    def _field_xml(self, field_uuid: str, rt_uuid: str, appian_type: str,
                    source_field_name: str, source_field_type: str,
                    field_name: str, display_name: str, is_record_id: bool = False) -> str:
        return f"""      <field>
        <uuid>{field_uuid}</uuid>
        <type>{appian_type}</type>
        <sourceFieldName>{source_field_name}</sourceFieldName>
        <sourceFieldType>{source_field_type}</sourceFieldType>
        <fieldName>{field_name}</fieldName>
        <displayName>{display_name}</displayName>
        <isRecordId>{'true' if is_record_id else 'false'}</isRecordId>
        <isUnique>{'true' if is_record_id else 'false'}</isUnique>
        <isCustomField>false</isCustomField>
        <customFieldExpr/>
        <customFieldDefaultValueStr>null</customFieldDefaultValueStr>
        <fieldCalculationType>NA</fieldCalculationType>
        <fieldTemplateType>NA</fieldTemplateType>
        <recordFieldSecurityMembershipFilter/>
        <fieldFormat/>
        <isIndexable>false</isIndexable>
        <subType>NA</subType>
        <displayNameSource>STATIC</displayNameSource>
        <descriptionSource>STATIC</descriptionSource>
        <compositePkPrecedence>-1</compositePkPrecedence>
        <isHidden>false</isHidden>
      </field>"""

    @staticmethod
    def _escape(text: str) -> str:
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))
