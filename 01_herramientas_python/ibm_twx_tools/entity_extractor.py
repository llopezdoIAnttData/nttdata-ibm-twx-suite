"""Extracts Business Objects, parameters and data types from a TWXPackage."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
from .twx_parser import TWXPackage, TWXArtifact


@dataclass
class BOField:
    name: str
    type_ref: str
    is_list: bool = False
    required: bool = False
    default: Optional[str] = None
    description: Optional[str] = None


@dataclass
class BusinessObject:
    name: str
    guid: Optional[str]
    namespace: Optional[str]
    description: Optional[str]
    parent: Optional[str] = None
    fields: list[BOField] = field(default_factory=list)
    source_path: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "guid": self.guid,
            "namespace": self.namespace,
            "description": self.description,
            "parent": self.parent,
            "fields": [
                {
                    "name": f.name,
                    "type": f.type_ref,
                    "is_list": f.is_list,
                    "required": f.required,
                    "default": f.default,
                    "description": f.description,
                }
                for f in self.fields
            ],
        }


class EntityExtractor:
    """Extracts all Business Objects and typed variables from a parsed TWX package."""

    def __init__(self, package: TWXPackage):
        self.package = package

    def extract(self) -> list[BusinessObject]:
        objects: list[BusinessObject] = []

        for artifact in self.package.artifacts:
            if artifact.artifact_type == "business_object" and artifact.tree:
                bo = self._parse_bo(artifact)
                if bo:
                    objects.append(bo)

        # Also scan BPDs and services for variable type definitions
        for artifact in self.package.artifacts:
            if artifact.artifact_type in ("business_process", "service") and artifact.tree:
                objects.extend(self._extract_inline_types(artifact))

        return objects

    def extract_variables(self) -> list[dict]:
        """Collects all variables declared across processes and services."""
        variables = []
        for artifact in self.package.artifacts:
            if artifact.artifact_type in ("business_process", "service", "human_task") and artifact.tree:
                root = artifact.tree.getroot()
                for el in root.iter():
                    local = el.tag.split("}")[-1]
                    if local in ("variable", "Variable", "parameter", "Parameter", "privateVariable"):
                        var = {
                            "artifact": artifact.name,
                            "artifact_type": artifact.artifact_type,
                            "name": el.get("name") or el.get("id", ""),
                            "type": el.get("type") or el.get("typeRef") or el.get("dataType", "ANY"),
                            "is_list": el.get("isList", "false").lower() == "true",
                            "is_input": el.get("isInput", "false").lower() == "true",
                            "is_output": el.get("isOutput", "false").lower() == "true",
                            "description": self._child_text(el, "description"),
                        }
                        variables.append(var)
        return variables

    # ------------------------------------------------------------------ private

    def _parse_bo(self, artifact: TWXArtifact) -> Optional[BusinessObject]:
        root = artifact.tree.getroot()
        name = (
            root.get("name")
            or root.get("id")
            or artifact.name
        )
        bo = BusinessObject(
            name=name,
            guid=artifact.guid,
            namespace=root.get("namespace") or root.get("targetNamespace"),
            description=artifact.description,
            parent=root.get("parentType") or root.get("superType"),
            source_path=artifact.path,
        )

        for el in root.iter():
            local = el.tag.split("}")[-1]
            if local in ("field", "attribute", "property", "Parameter", "element"):
                field_name = el.get("name") or el.get("id", "")
                if not field_name:
                    continue
                field_type = (
                    el.get("type")
                    or el.get("typeRef")
                    or el.get("dataType")
                    or "String"
                )
                bo_field = BOField(
                    name=field_name,
                    type_ref=field_type,
                    is_list=el.get("isList", "false").lower() == "true",
                    required=el.get("required", "false").lower() == "true",
                    default=el.get("default") or el.get("defaultValue"),
                    description=self._child_text(el, "description"),
                )
                bo.fields.append(bo_field)

        return bo if bo.fields else bo

    def _extract_inline_types(self, artifact: TWXArtifact) -> list[BusinessObject]:
        """Picks up anonymous/inline type definitions embedded in process/service XMLs."""
        objects: list[BusinessObject] = []
        root = artifact.tree.getroot()

        for el in root.iter():
            local = el.tag.split("}")[-1]
            if local in ("complexType", "inlineType", "embeddedType"):
                name = el.get("name") or el.get("id", "")
                if not name:
                    continue
                bo = BusinessObject(
                    name=f"{artifact.name}::{name}",
                    guid=el.get("id"),
                    namespace=None,
                    description=self._child_text(el, "description"),
                    source_path=artifact.path,
                )
                for child in el:
                    child_local = child.tag.split("}")[-1]
                    if child_local in ("field", "attribute", "element"):
                        bo.fields.append(BOField(
                            name=child.get("name", ""),
                            type_ref=child.get("type") or child.get("typeRef", "String"),
                        ))
                objects.append(bo)

        return objects

    @staticmethod
    def _child_text(el: ET.Element, tag: str) -> Optional[str]:
        for child in el:
            if child.tag.split("}")[-1] == tag and child.text:
                return child.text.strip()
        return None
