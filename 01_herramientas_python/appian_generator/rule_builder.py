"""
rule_builder.py — IBM BPM Service → Appian Expression Rule XML

Based on real Appian v26.3 rule structure from NCI Redención Bono package.

Real structure inside content/<uuid>.xml:
    <contentHaul xmlns:a="http://www.appian.com/ae/types/2009">
        <versionUuid>...</versionUuid>
        <rule>
            <name>NCI_RB_MapStartSubstageRedencion</name>
            <uuid>...</uuid>
            <description>Start Substage Integration Map</description>
            <parentUuid>...</parentUuid>
            <visibility>...</visibility>
            <ruleInput>
                <name>idArchivo_int</name>
                <type><name>int</name><namespace>http://www.w3.org/2001/XMLSchema</namespace></type>
            </ruleInput>
            <definition>a!localVariables(...</definition>
        </rule>
        <roleMap>...</roleMap>
        <history>...</history>
    </contentHaul>

IBM IS → Appian Rule mapping:
  - IS name → rule name (with app prefix)
  - IS input variables → ruleInput elements
  - IS output variables → NOT in rule signature (return value is the expression)
  - IS JavaScript logic → Appian Expression Language (requires LLM for complex logic)
  - Simple IS (single step, no JS) → stub rule with TODO comment
"""

from dataclasses import dataclass, field as dc_field
from typing import Optional
from .uuid_registry import UUIDRegistry

APPIAN_NS = "http://www.appian.com/ae/types/2009"
XSD_NS = "http://www.w3.org/2001/XMLSchema"

# IBM → Appian type for rule inputs
IBM_TO_RULE_INPUT_TYPE = {
    "string":   ("string",  XSD_NS),
    "String":   ("string",  XSD_NS),
    "int":      ("int",     XSD_NS),
    "integer":  ("int",     XSD_NS),
    "Integer":  ("int",     XSD_NS),
    "long":     ("long",    XSD_NS),
    "decimal":  ("decimal", XSD_NS),
    "Decimal":  ("decimal", XSD_NS),
    "boolean":  ("boolean", XSD_NS),
    "Boolean":  ("boolean", XSD_NS),
    "date":     ("date",    XSD_NS),
    "dateTime": ("dateTime", XSD_NS),
    "Date":     ("date",    XSD_NS),
    "DateTime": ("dateTime", XSD_NS),
    "ANY":      ("Variant", APPIAN_NS),
    "Object":   ("Variant", APPIAN_NS),
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
class RuleInput:
    """A rule input parameter."""
    name: str
    type_name: str = "string"
    type_ns: str = XSD_NS
    description: str = ""
    is_list: bool = False


@dataclass
class AppianRule:
    """An Appian Expression Rule ready for serialization."""
    name: str
    uuid: str
    description: str = ""
    parent_uuid: str = ""
    inputs: list = dc_field(default_factory=list)
    definition: str = ""
    version_uuid: str = ""
    source_ibm_name: str = ""

    def __post_init__(self):
        if not self.version_uuid:
            self.version_uuid = self.uuid


class RuleBuilder:
    """
    Builds Appian Expression Rule XML from IBM BPM service metadata.

    For the initial migration, we generate STUB rules with:
    - Correct name and inputs
    - A TODO comment in the definition pointing to the IBM IS name
    - This gives a valid importable rule that developers can fill in

    Usage:
        builder = RuleBuilder(registry, app_prefix="NCI_RB")
        rule = builder.create_stub_rule(
            name="MapStartSubstage",
            description="Maps start substage request",
            inputs=[RuleInput("idArchivo_int", "int"), RuleInput("option_int", "int")],
            ibm_service_name="IG MapStartSubstage"
        )
        xml = builder.to_xml(rule)
    """

    def __init__(self, registry: UUIDRegistry, app_prefix: str = "NCI_RB",
                 default_parent_uuid: str = ""):
        self.registry = registry
        self.app_prefix = app_prefix
        self.default_parent_uuid = default_parent_uuid

    def create_stub_rule(self, name: str, description: str = "",
                          inputs: list = None,
                          ibm_service_name: str = "",
                          parent_uuid: str = "",
                          definition: str = "") -> AppianRule:
        """
        Create a stub Appian Expression Rule.

        The definition will be a placeholder that clearly indicates what
        IBM logic needs to be translated.
        """
        appian_name = self._normalize_name(name)
        uuid_str = self.registry.get_or_create(f"RULE:{appian_name}")

        if not definition:
            # Generate a stub definition with clear TODO instructions
            input_list = ", ".join(f"ri!{inp.name}" for inp in (inputs or []))
            ibm_ref = f"IBM IS: {ibm_service_name}" if ibm_service_name else "IBM service"
            definition = f"""/* ============================================================
   TODO: Translate logic from {ibm_ref}
   
   Inputs available: {input_list or 'none'}
   
   This is a generated stub. Replace this comment with the
   Appian Expression Language equivalent of the IBM logic.
   ============================================================ */
null"""

        return AppianRule(
            name=appian_name,
            uuid=uuid_str,
            description=description or f"Auto-generated stub for IBM service: {ibm_service_name or name}",
            parent_uuid=parent_uuid or self.default_parent_uuid,
            inputs=inputs or [],
            definition=definition,
            source_ibm_name=ibm_service_name,
        )

    def from_ibm_service(self, service_name: str, service_description: str = "",
                          input_vars: list = None,
                          ibm_definition: str = "",
                          parent_uuid: str = "") -> AppianRule:
        """
        Create an Appian rule from IBM IS metadata.

        Args:
            service_name: IBM service name
            service_description: IBM service description
            input_vars: List of (name, type) tuples for inputs
            ibm_definition: IBM JavaScript logic (for reference in stub)
            parent_uuid: Parent folder UUID in Appian
        """
        inputs = []
        for var in (input_vars or []):
            if isinstance(var, tuple) and len(var) == 2:
                var_name, var_type = var
            elif isinstance(var, RuleInput):
                inputs.append(var)
                continue
            else:
                var_name, var_type = str(var), "string"

            type_name, type_ns = IBM_TO_RULE_INPUT_TYPE.get(var_type, ("string", XSD_NS))
            inputs.append(RuleInput(name=var_name, type_name=type_name, type_ns=type_ns))

        definition = ""
        if ibm_definition:
            # Include IBM logic as a comment reference
            truncated = ibm_definition[:500] + "..." if len(ibm_definition) > 500 else ibm_definition
            definition = f"""/* IBM JavaScript Logic (translate to Appian EL):
{truncated}
*/
null"""

        return self.create_stub_rule(
            name=service_name,
            description=service_description,
            inputs=inputs,
            ibm_service_name=service_name,
            parent_uuid=parent_uuid,
            definition=definition,
        )

    def to_xml(self, rule: AppianRule) -> str:
        """Serialize an AppianRule to contentHaul XML."""
        inputs_xml = "\n".join(self._input_to_xml(inp) for inp in rule.inputs)
        parent_xml = f"<parentUuid>{rule.parent_uuid}</parentUuid>" if rule.parent_uuid else ""
        definition_escaped = self._escape(rule.definition)

        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<contentHaul xmlns:a="{APPIAN_NS}">
    <versionUuid>{rule.version_uuid}</versionUuid>
    <rule>
        <name>{self._escape(rule.name)}</name>
        <uuid>{rule.uuid}</uuid>
        <description>{self._escape(rule.description)}</description>
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
{inputs_xml}
        <definition>{definition_escaped}</definition>
    </rule>
{ROLE_MAP_TEMPLATE}
    <history>
        <historyInfo versionUuid="{rule.version_uuid}"/>
    </history>
</contentHaul>"""

    def _input_to_xml(self, inp: RuleInput) -> str:
        """Generate XML for a single rule input."""
        return f"""        <ruleInput>
            <name>{self._escape(inp.name)}</name>
            <description>{self._escape(inp.description)}</description>
            <type>
                <name>{inp.type_name}</name>
                <namespace>{inp.type_ns}</namespace>
            </type>
        </ruleInput>"""

    def _normalize_name(self, name: str) -> str:
        """Add app prefix if not present."""
        prefix = f"{self.app_prefix}_"
        if not name.startswith(prefix):
            # Clean name: replace spaces and special chars with underscore
            clean = name.replace(" ", "_").replace("-", "_")
            return f"{prefix}{clean}"
        return name

    @staticmethod
    def _escape(text: str) -> str:
        return (str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))
