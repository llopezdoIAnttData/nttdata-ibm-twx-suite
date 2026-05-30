"""
process_model_builder.py — IBM BPM BPD → Appian Process Model XML

Generates a STUB Appian process model from an IBM BPD:
  - Correct name (with prefix)
  - Process variables from IBM BPD parameters (inputs/outputs)
  - Minimal flow: Start Node → Script Task (TODO placeholder) → End Node
  - Folder UUID reference

This is the "least invasive" approach: creates all the scaffolding so
developers can open the process in Appian Designer and implement the logic
without creating anything from scratch.

IBM → Appian mapping:
  BPD name          → process model name (with prefix)
  bpdParameter (1)  → pv name with parameter=true, required=true  (inputs)
  bpdParameter (2)  → pv name with parameter=false               (outputs)
  classId → BO name → look up UUID in registry → CDT type reference
"""

from dataclasses import dataclass, field as dc_field
from typing import Optional
from .uuid_registry import UUIDRegistry

APPIAN_NS = "http://www.appian.com/ae/types/2009"
XSD_NS    = "http://www.w3.org/2001/XMLSchema"
CDT_NS    = "urn:com:appian:recordtype:datatype"

# IBM XSD types → Appian process variable xsi:type
IBM_PV_TYPE_MAP = {
    "string":   ("xsd:string",   None),
    "String":   ("xsd:string",   None),
    "int":      ("xsd:int",      None),
    "integer":  ("xsd:int",      None),
    "Integer":  ("xsd:int",      None),
    "long":     ("xsd:long",     None),
    "decimal":  ("xsd:decimal",  None),
    "Decimal":  ("xsd:decimal",  None),
    "float":    ("xsd:decimal",  None),
    "double":   ("xsd:decimal",  None),
    "boolean":  ("xsd:boolean",  None),
    "Boolean":  ("xsd:boolean",  None),
    "date":     ("xsd:date",     None),
    "dateTime": ("xsd:dateTime", None),
    "Date":     ("xsd:date",     None),
}

ROLE_MAP = """  <roleMap>
    <role name="ADMIN_OWNER"><users/><groups/></role>
    <role name="EDITOR"><users/><groups/></role>
    <role name="EXPLICIT_NONMEMBER"><users/><groups/></role>
    <role name="VIEWER"><users/><groups/></role>
    <role name="MANAGER"><users/><groups/></role>
    <role name="INITIATOR"><users/><groups/></role>
  </roleMap>"""

NODE_LABEL = """          <label>
            <fontColor>#000000</fontColor>
            <fontFamily>Appian Open Sans, Sans-Serif</fontFamily>
            <fontSize>12</fontSize>
            <bold>false</bold>
            <italics>false</italics>
            <underline>false</underline>
          </label>
          <deadline><enabled>false</enabled><type>0</type><units>0</units><rex/><aex/></deadline>
          <allowsBack>false</allowsBack>
          <refreshDefaultValues>false</refreshDefaultValues>
          <on-complete-keep-form-data>false</on-complete-keep-form-data>
          <skipNotification>false</skipNotification>"""

NODE_TAIL = """          <multiple-instance/>
          <escalations/>"""

NODE_FOOTER = """          <associations/>
          <target-completion>5.0</target-completion>
          <target-lag>1.0</target-lag>
          <attachments/>
          <notes/>
          <lingering>false</lingering>
          <on-create-ignore-if-active>false</on-create-ignore-if-active>
          <on-create-delete-previous-active>false</on-create-delete-previous-active>
          <on-complete-delete-previous-completed>false</on-complete-delete-previous-completed>
          <pre-triggers/><post-triggers/><event-producers/><exception-flow/>"""

# ACPs required by End Node (core.1) — from real Appian reference model
END_NODE_ACPS = """            <acps>
              <acp name="pmID">
                <a:value xsi:nil="true" xsi:type="a:ProcessModel"/>
                <a:local-id>0</a:local-id><a:expr/><a:required>0</a:required>
                <a:editable>0</a:editable><a:assign-to-pv/>
                <a:input-to-activity-class>true</a:input-to-activity-class>
                <a:hidden-from-designer>false</a:hidden-from-designer>
                <a:generated>false</a:generated><a:enumeration/><a:customDisplayReference/>
              </acp>
              <acp name="inMap">
                <a:value xsi:nil="true" xsi:type="a:Bean?list"/>
                <a:local-id>1</a:local-id><a:expr/><a:required>0</a:required>
                <a:editable>1</a:editable><a:assign-to-pv/>
                <a:input-to-activity-class>true</a:input-to-activity-class>
                <a:hidden-from-designer>false</a:hidden-from-designer>
                <a:generated>false</a:generated><a:enumeration/><a:customDisplayReference/>
              </acp>
              <acp name="procInheritsPriority">
                <a:value xmlns="" xsi:type="xsd:int">1</a:value>
                <a:local-id>5</a:local-id><a:expr/><a:required>0</a:required>
                <a:editable>1</a:editable><a:assign-to-pv/>
                <a:input-to-activity-class>false</a:input-to-activity-class>
                <a:hidden-from-designer>false</a:hidden-from-designer>
                <a:generated>false</a:generated><a:enumeration/><a:customDisplayReference/>
              </acp>
              <acp name="pmUUID">
                <a:value xsi:nil="true" xsi:type="xsd:string"/>
                <a:local-id>6</a:local-id><a:expr/><a:required>0</a:required>
                <a:editable>1</a:editable><a:assign-to-pv/>
                <a:input-to-activity-class>true</a:input-to-activity-class>
                <a:hidden-from-designer>false</a:hidden-from-designer>
                <a:generated>false</a:generated><a:enumeration/><a:customDisplayReference/>
              </acp>
              <acp name="isAsynchronous">
                <a:value xmlns="" xsi:type="xsd:boolean">true</a:value>
                <a:local-id>7</a:local-id><a:expr/><a:required>1</a:required>
                <a:editable>0</a:editable><a:assign-to-pv/>
                <a:input-to-activity-class>true</a:input-to-activity-class>
                <a:hidden-from-designer>true</a:hidden-from-designer>
                <a:generated>false</a:generated><a:enumeration/><a:customDisplayReference/>
              </acp>
              <acp name="isTransparent">
                <a:value xmlns="" xsi:type="xsd:boolean">true</a:value>
                <a:local-id>14</a:local-id><a:expr/><a:required>1</a:required>
                <a:editable>1</a:editable><a:assign-to-pv/>
                <a:input-to-activity-class>true</a:input-to-activity-class>
                <a:hidden-from-designer>true</a:hidden-from-designer>
                <a:generated>false</a:generated><a:enumeration/><a:customDisplayReference/>
              </acp>
              <acp name="inheritSecurity">
                <a:value xmlns="" xsi:type="xsd:boolean">false</a:value>
                <a:local-id>15</a:local-id><a:expr/><a:required>1</a:required>
                <a:editable>1</a:editable><a:assign-to-pv/>
                <a:input-to-activity-class>true</a:input-to-activity-class>
                <a:hidden-from-designer>true</a:hidden-from-designer>
                <a:generated>false</a:generated><a:enumeration/><a:customDisplayReference/>
              </acp>
            </acps>"""

FORM_MAP_PM = """      <form-map>
        <pair>
          <locale country="MX" lang="es" variant=""/>
          <form-config><form><type>3</type><enabled>false</enabled>
            <dynamic-form><form-elements/></dynamic-form>
            <hiddenSections>16</hiddenSections></form></form-config>
        </pair>
        <pair>
          <locale country="US" lang="en" variant=""/>
          <form-config><form><type>3</type><enabled>true</enabled>
            <dynamic-form><form-elements/></dynamic-form>
            <hiddenSections>16</hiddenSections></form></form-config>
        </pair>
      </form-map>"""

CONNECTION_TEMPLATE = """            <connection>
              <guiId>{conn_id}</guiId>
              <to>{to_gui}</to>
              <toObjectType>ap.gui.Node</toObjectType>
              <fromAnchor/><toAnchor/>
              <showArrowhead>true</showArrowhead>
              <flowLabel/>
              <label>
                <fontColor>#000</fontColor>
                <fontFamily>Appian Open Sans, Sans-Serif</fontFamily>
                <fontSize>12</fontSize>
                <bold>false</bold><italics>false</italics><underline>false</underline>
              </label>
              <associations/>
              <chained>false</chained>
              <overridesAssignment>true</overridesAssignment>
              <synchronizeData>false</synchronizeData>
            </connection>"""


@dataclass
class AppianProcessModel:
    """An Appian Process Model ready for serialization."""
    name: str
    uuid: str
    version_uuid: str
    folder_uuid: str
    description: str = ""
    source_ibm_name: str = ""
    pvs: list = dc_field(default_factory=list)   # list of (name, type_decl, is_input, is_list)


class ProcessModelBuilder:
    """
    Builds Appian Process Model XML stubs from IBM BPD metadata.

    Usage:
        builder = ProcessModelBuilder(registry, app_prefix="NCI_RB",
                                      folder_uuid="...", admin_group_uuid="...")
        pm = builder.from_ibm_process(ibm_process, bos)
        xml = builder.to_xml(pm)
    """

    def __init__(self, registry: UUIDRegistry, app_prefix: str = "",
                 folder_uuid: str = "", admin_group_uuid: str = ""):
        self.registry = registry
        self.app_prefix = app_prefix
        self.folder_uuid = folder_uuid
        self.admin_group_uuid = admin_group_uuid

    def from_ibm_process(self, process, bos: list) -> AppianProcessModel:
        """
        Create an Appian Process Model stub from an IBM BPD.

        Args:
            process: IBMProcess dataclass instance
            bos:     list of IBMBusinessObject (to resolve BO type references)
        """
        prefix = f"{self.app_prefix}_" if self.app_prefix else ""
        clean = process.name.replace(" ", "_").replace("-", "_")
        appian_name = f"{prefix}{clean}" if not process.name.startswith(prefix) else process.name

        uuid_str = self.registry.get_or_create(f"PM:{appian_name}")
        # PM_VER4 — bump this prefix each time a structural fix is applied so that
        # Appian treats the import as an UPDATE (not "Not Updated").
        version_uuid = self.registry.get_or_create(f"PM_VER4:{appian_name}")

        # Build BO name → UUID map for type resolution
        bo_by_name = {bo.name: self.registry.get_or_create(f"RT:{bo.name}") for bo in bos}

        # Build process variables — deduplicate by case-insensitive name.
        # IBM BPDs can have the same param as both input and output (param_type 1 and 2).
        # Appian rejects duplicate PV names (case-insensitive), so we keep the first
        # occurrence (input wins over output when both share the same name).
        pvs = []
        seen_pv_lower: set = set()
        for param in process.params:
            key = param.name.lower()
            if key in seen_pv_lower:
                continue
            seen_pv_lower.add(key)
            pv_type_decl = self._resolve_pv_type(param, bo_by_name)
            is_input = (param.param_type == 1)
            pvs.append((param.name, pv_type_decl, is_input, param.is_array))

        return AppianProcessModel(
            name=appian_name,
            uuid=uuid_str,
            version_uuid=version_uuid,
            folder_uuid=self.folder_uuid,
            description=process.description or f"Migrated from IBM BPD: {process.name}",
            source_ibm_name=process.name,
            pvs=pvs,
        )

    def _resolve_pv_type(self, param, bo_by_name: dict) -> str:
        """
        Returns the xsi:type declaration string and optional namespace prefix declaration
        for a process variable.

        Returns a tuple (type_decl_attrs, ns_decl) where:
          type_decl_attrs: XML attributes like xsi:type="xsd:string"
          ns_decl: optional namespace declaration like xmlns:n1="..."
        """
        # Try to resolve via class_id → BO name → Registry UUID
        if param.class_id:
            # classId format: "namespace/12.uuid" — extract BO ID
            bo_ref = param.class_id.split("/")[-1] if "/" in param.class_id else param.class_id
            # Search bo_by_name for a matching ID
            # The registry key is "RT:{bo_name}" → if we have the BO name, look it up
            # Try to find BO by name in registry
            for bo_name, bo_uuid in bo_by_name.items():
                rt_key = f"RT:{bo_name}"
                if self.registry.get_or_create(rt_key) == bo_uuid:
                    if param.is_array:
                        return f'xmlns:n1="{CDT_NS}" xsi:nil="true" xsi:type="n1:{bo_uuid}?list"'
                    return f'xmlns:n1="{CDT_NS}" xsi:nil="true" xsi:type="n1:{bo_uuid}"'

        # Check XSD built-in type from name suffix heuristics
        name_lower = param.name.lower()
        if name_lower.endswith("_int") or name_lower.endswith("_num"):
            xsd = "xsd:int"
        elif name_lower.endswith("_dec") or name_lower.endswith("_amt"):
            xsd = "xsd:decimal"
        elif name_lower.endswith("_bool") or name_lower.endswith("_flag"):
            xsd = "xsd:boolean"
        elif name_lower.endswith("_date") or name_lower.endswith("_dt"):
            xsd = "xsd:date"
        elif name_lower.endswith("_datetime"):
            xsd = "xsd:dateTime"
        else:
            xsd = "xsd:string"

        if param.is_array:
            return f'xmlns="" xsi:type="{xsd}?list"'
        return f'xmlns="" xsi:type="{xsd}"'

    def _build_pv_xml(self, pvs: list) -> str:
        """Build <pvs> section XML."""
        if not pvs:
            return "      <pvs/>"

        lines = ["      <pvs>"]
        for (pv_name, type_attrs, is_input, is_array) in pvs:
            lines.append(f"""        <pv name="{self._esc(pv_name)}">
          <a:value {type_attrs}/>
          <parameter>{"true" if is_input else "false"}</parameter>
          <required>{"true" if is_input else "false"}</required>
          <hidden>false</hidden>
        </pv>""")
        lines.append("      </pvs>")
        return "\n".join(lines)

    def _build_nodes_xml(self, pm: AppianProcessModel) -> str:
        """Build Start → End → Script Task nodes (order matches real Appian reference)."""
        start_uuid  = self.registry.get_or_create(f"PM_NODE_START:{pm.uuid}")
        end_uuid    = self.registry.get_or_create(f"PM_NODE_END:{pm.uuid}")
        script_uuid = self.registry.get_or_create(f"PM_NODE_SCRIPT:{pm.uuid}")

        start_conn  = CONNECTION_TEMPLATE.format(conn_id=1, to_gui=2)
        script_conn = CONNECTION_TEMPLATE.format(conn_id=2, to_gui=1)

        return f"""      <nodes>
        <node uuid="{start_uuid}">
          <guiId>0</guiId>
          <owner/>
          <icon id="50"/>
          <picon id="0"/>
          <fname>
            <string-map>
              <pair><locale country="US" lang="en" variant=""/><value><![CDATA[Start Node]]></value></pair>
              <pair><locale country="MX" lang="es" variant=""/><value><![CDATA[Start Node]]></value></pair>
            </string-map>
          </fname>
          <x>112</x><y>112</y>
          <display>
            <string-map>
              <pair><locale country="US" lang="en" variant=""/><value><![CDATA[Start Node]]></value></pair>
              <pair><locale country="MX" lang="es" variant=""/><value><![CDATA[Start Node]]></value></pair>
            </string-map>
          </display>
          <desc>
            <string-map>
              <pair><locale country="US" lang="en" variant=""/><value/></pair>
              <pair><locale country="MX" lang="es" variant=""/><value/></pair>
            </string-map>
          </desc>
          <notify>false</notify>
          <confirmation-url/>
          <lane/>
          <overrideLaneAssignment>false</overrideLaneAssignment>
          <ac>
            <local-id>core.0</local-id>
            <name><![CDATA[Start Node]]></name>
            <acps/><custom-params/><output-exprs/>
            <requires-user-interaction>true</requires-user-interaction>
            <run-as><performer id="0"/></run-as>
            <form-map/><helper-class/>
          </ac>
          <multiple-instance/>
          <escalations/>
          <connections>
{start_conn}
          </connections>
{NODE_FOOTER}
{NODE_LABEL}
        </node>
        <node uuid="{end_uuid}">
          <guiId>1</guiId>
          <owner/>
          <icon id="51"/>
          <picon id="0"/>
          <fname>
            <string-map>
              <pair><locale country="US" lang="en" variant=""/><value><![CDATA[End Node]]></value></pair>
              <pair><locale country="MX" lang="es" variant=""/><value><![CDATA[End Node]]></value></pair>
            </string-map>
          </fname>
          <x>812</x><y>112</y>
          <display>
            <string-map>
              <pair><locale country="US" lang="en" variant=""/><value><![CDATA[End Node]]></value></pair>
              <pair><locale country="MX" lang="es" variant=""/><value><![CDATA[End Node]]></value></pair>
            </string-map>
          </display>
          <desc>
            <string-map>
              <pair><locale country="US" lang="en" variant=""/><value/></pair>
              <pair><locale country="MX" lang="es" variant=""/><value/></pair>
            </string-map>
          </desc>
          <notify>false</notify>
          <confirmation-url/>
          <lane/>
          <overrideLaneAssignment>false</overrideLaneAssignment>
          <ac>
            <local-id>core.1</local-id>
            <name><![CDATA[End Node]]></name>
{END_NODE_ACPS}
            <custom-params/><output-exprs/>
            <requires-user-interaction>true</requires-user-interaction>
            <run-as><performer id="0"/></run-as>
            <form-map/><helper-class/>
          </ac>
          <multiple-instance/>
          <escalations/>
          <connections/>
{NODE_FOOTER}
{NODE_LABEL}
        </node>
        <node uuid="{script_uuid}">
          <guiId>2</guiId>
          <owner/>
          <icon id="68"/>
          <picon id="69"/>
          <fname>
            <string-map>
              <pair><locale country="US" lang="en" variant=""/><value><![CDATA[Script Task]]></value></pair>
              <pair><locale country="MX" lang="es" variant=""/><value/></pair>
            </string-map>
          </fname>
          <x>364</x><y>112</y>
          <display>
            <string-map>
              <pair><locale country="US" lang="en" variant=""/><value><![CDATA[TODO: {self._esc(pm.source_ibm_name)}]]></value></pair>
              <pair><locale country="MX" lang="es" variant=""/><value/></pair>
            </string-map>
          </display>
          <desc>
            <string-map>
              <pair><locale country="US" lang="en" variant=""/><value><![CDATA[Migrated from IBM BPD: {self._esc(pm.source_ibm_name)}]]></value></pair>
              <pair><locale country="MX" lang="es" variant=""/><value/></pair>
            </string-map>
          </desc>
          <notify>false</notify>
          <confirmation-url/>
          <lane/>
          <overrideLaneAssignment>false</overrideLaneAssignment>
          <ac>
            <local-id>internal.16</local-id>
            <name><![CDATA[Unattended Multiple Questions]]></name>
            <acps/><custom-params/><output-exprs/>
            <requires-user-interaction>true</requires-user-interaction>
            <run-as><performer id="0"/></run-as>
            <form-map/><helper-class/>
          </ac>
          <multiple-instance/>
          <escalations/>
          <connections>
{script_conn}
          </connections>
{NODE_FOOTER}
{NODE_LABEL}
        </node>
      </nodes>"""

    def to_xml(self, pm: AppianProcessModel) -> str:
        """Serialize an AppianProcessModel to processModelHaul XML."""
        pvs_xml    = self._build_pv_xml(pm.pvs)
        nodes_xml  = self._build_nodes_xml(pm)
        folder     = pm.folder_uuid or "00000000-0000-0000-0000-000000000000"
        admin_grp  = self.admin_group_uuid

        admin_groups_xml = ""
        if admin_grp:
            admin_groups_xml = f"<groupUuid>{admin_grp}</groupUuid>"

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<processModelHaul>
  <versionUuid>{pm.version_uuid}</versionUuid>
  <folderUuid>{folder}</folderUuid>
  <roleMap>
    <role name="ADMIN_OWNER">
      <users/>
      <groups>{admin_groups_xml}</groups>
    </role>
    <role name="EDITOR"><users/><groups/></role>
    <role name="EXPLICIT_NONMEMBER"><users/><groups/></role>
    <role name="VIEWER"><users/><groups/></role>
    <role name="MANAGER"><users/><groups/></role>
    <role name="INITIATOR"><users/><groups/></role>
  </roleMap>
  <process_model_port schemaVersion="007.000.004"
    xmlns="http://www.appian.com/ae/types/2009"
    xmlns:a="http://www.appian.com/ae/types/2009"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <pm>
      <meta>
        <uuid><![CDATA[{pm.uuid}]]></uuid>
        <name>
          <string-map>
            <pair>
              <locale country="US" lang="en" variant=""/>
              <value><![CDATA[{self._esc(pm.name)}]]></value>
            </pair>
            <pair>
              <locale country="MX" lang="es" variant=""/>
              <value/>
            </pair>
          </string-map>
        </name>
        <desc>
          <string-map>
            <pair>
              <locale country="US" lang="en" variant=""/>
              <value><![CDATA[{self._esc(pm.description)}]]></value>
            </pair>
            <pair>
              <locale country="MX" lang="es" variant=""/>
              <value/>
            </pair>
          </string-map>
        </desc>
        <versionStatus>2</versionStatus>
        <process-name>
          <string-map>
            <pair>
              <locale country="US" lang="en" variant=""/>
              <value><![CDATA[{self._esc(pm.name)}]]></value>
            </pair>
            <pair>
              <locale country="MX" lang="es" variant=""/>
              <value/>
            </pair>
          </string-map>
        </process-name>
        <deadline>
          <enabled>false</enabled>
          <type>0</type>
          <units>0</units>
          <rex/>
          <aex/>
        </deadline>
        <pm-notification-settings>
          <custom-settings>false</custom-settings>
          <notify-initiator>false</notify-initiator>
          <notify-owner>false</notify-owner>
          <usersandgroups/>
          <recipients-exp/>
        </pm-notification-settings>
        <cleanup-action>2</cleanup-action>
        <auto-archive-delay>7</auto-archive-delay>
        <auto-delete-delay>0</auto-delete-delay>
        <timeZoneId><![CDATA[America/Mexico_City]]></timeZoneId>
        <useProcessInitiatorTimeZone>true</useProcessInitiatorTimeZone>
      </meta>
{pvs_xml}
{nodes_xml}
      <annotations/>
      <lanes/>
      <attachments/>
      <notes/>
      <priority id="1"/>
{FORM_MAP_PM}
      <isPublic>false</isPublic>
      <isEPEx>false</isEPEx>
    </pm>
  </process_model_port>
  <isPublished>true</isPublished>
  <history>
    <historyInfo versionUuid="{pm.version_uuid}"/>
  </history>
</processModelHaul>"""

    def build_f3_process_set(self, process, bos: list, async_points: list[dict]) -> list[AppianProcessModel]:
        """
        Build a set of F3-architecture ephemeral process model stubs from a single IBM BPD.

        Instead of one long-lived process, F3 decomposes each BPD into:
          - N+1 launcher process stubs (one per async break point + final)
          - 1 shared NOV Respuesta Bus stub

        Args:
            process:       IBMProcess dataclass instance
            bos:           list of IBMBusinessObject (for type resolution)
            async_points:  list of dicts with keys: step_id, is_name, uca_name
                           (from ParametriaExtractor output)

        Returns:
            list of AppianProcessModel — import each one separately
        """
        models: list[AppianProcessModel] = []
        prefix = f"{self.app_prefix}_" if self.app_prefix else ""
        bpd_clean = process.name.replace(" ", "").replace("-", "")
        bo_by_name = {bo.name: self.registry.get_or_create(f"RT:{bo.name}") for bo in bos}

        n_async = len(async_points)

        # Build launcher stubs for each step
        for i in range(n_async + 1):
            step_id = i + 1
            is_last = (i == n_async)
            if is_last:
                appian_name = f"{prefix}NOV_{bpd_clean}_Finalizar"
                description = f"F3 paso final — cierre del flujo. IBM: {process.name}"
            else:
                ap = async_points[i]
                appian_name = f"{prefix}NOV_{bpd_clean}_Paso{step_id}"
                is_name = ap.get("is_name", f"IS Paso{step_id}")
                uca_name = ap.get("uca_name", "UCA")
                description = (
                    f"F3 paso {step_id} (efímero). Lanza integración, guarda estado en "
                    f"NOV_INSTANCE_MANAGEMENT y termina. IBM: {is_name} → espera {uca_name}. "
                    f"BPD: {process.name}"
                )

            uuid_str = self.registry.get_or_create(f"PM:{appian_name}")
            version_uuid = self.registry.get_or_create(f"PM_VER4:{appian_name}")

            # Standard PVs: folio + action_out + status_id (minimum F3 contract)
            pvs = [
                ("folio",      'xmlns="" xsi:type="xsd:string"',  True,  False),
                ("accion_out", 'xmlns="" xsi:type="xsd:int"',     False, False),
                ("status_id",  'xmlns="" xsi:type="xsd:boolean"', False, False),
            ]

            models.append(AppianProcessModel(
                name=appian_name,
                uuid=uuid_str,
                version_uuid=version_uuid,
                folder_uuid=self.folder_uuid,
                description=description,
                source_ibm_name=process.name,
                pvs=pvs,
            ))

        # Add NOV Respuesta Bus stub (shared dispatcher)
        bus_name = f"{prefix}NOV_RespuestaBus_{bpd_clean}"
        bus_uuid = self.registry.get_or_create(f"PM:{bus_name}")
        bus_ver_uuid = self.registry.get_or_create(f"PM_VER4:{bus_name}")
        models.append(AppianProcessModel(
            name=bus_name,
            uuid=bus_uuid,
            version_uuid=bus_ver_uuid,
            folder_uuid=self.folder_uuid,
            description=(
                f"F3 dispatcher. Recibe respuesta IIB/BUS, actualiza NOV_INSTANCE_MANAGEMENT, "
                f"lee parametría y lanza el siguiente proceso efímero. BPD origen: {process.name}"
            ),
            source_ibm_name=process.name,
            pvs=[
                ("folio",      'xmlns="" xsi:type="xsd:string"',  True,  False),
                ("id_instancia",'xmlns="" xsi:type="xsd:int"',    True,  False),
                ("response_out",'xmlns="" xsi:type="xsd:string"', False, False),
                ("accion_out", 'xmlns="" xsi:type="xsd:int"',     False, False),
            ],
        ))

        return models

    def build_pm_folder(self, folder_uuid: str) -> str:
        """Build processModelFolderHaul XML."""
        version_uuid = self.registry.get_or_create(f"PM_FOLDER_VER:{folder_uuid}")
        prefix = self.app_prefix or "APP"
        admin_grp = self.admin_group_uuid
        admin_groups_xml = f"<groupUuid>{admin_grp}</groupUuid>" if admin_grp else ""

        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<processModelFolderHaul xmlns:a="{APPIAN_NS}">
    <versionUuid>{version_uuid}</versionUuid>
    <processModelFolder>
        <name>{prefix} Process Models</name>
        <uuid>{folder_uuid}</uuid>
        <description>Process models migrated from IBM BPM — {prefix}</description>
    </processModelFolder>
    <roleMap>
        <role name="ADMIN_OWNER">
            <users/>
            <groups>{admin_groups_xml}</groups>
        </role>
        <role name="EDITOR"><users/><groups/></role>
        <role name="EXPLICIT_NONMEMBER"><users/><groups/></role>
        <role name="VIEWER"><users/><groups/></role>
        <role name="MANAGER"><users/><groups/></role>
        <role name="INITIATOR"><users/><groups/></role>
    </roleMap>
    <history>
        <historyInfo versionUuid="{version_uuid}"/>
    </history>
</processModelFolderHaul>"""

    @staticmethod
    def _esc(text: str) -> str:
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
