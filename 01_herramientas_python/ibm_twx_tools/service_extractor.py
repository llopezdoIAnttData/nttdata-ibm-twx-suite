"""Extracts services, scripts, integrations and their logic from a TWXPackage."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
from .twx_parser import TWXPackage, TWXArtifact


SERVICE_STEP_TYPES = {
    "scriptTask":     "Script",
    "serviceTask":    "Service Call",
    "systemTask":     "System Task",
    "userTask":       "Human Task",
    "decisionTask":   "Decision",
    "integrationTask": "Integration",
    "startEvent":     "Start",
    "endEvent":       "End",
    "gatewayNode":    "Gateway",
    "intermediateEvent": "Intermediate Event",
    "subProcess":     "Sub-Process",
    "callActivity":   "Call Activity",
}


@dataclass
class ServiceStep:
    step_id: str
    name: str
    step_type: str
    script: Optional[str] = None
    called_service: Optional[str] = None
    inputs: list[dict] = field(default_factory=list)
    outputs: list[dict] = field(default_factory=list)
    condition: Optional[str] = None
    error_handler: bool = False


@dataclass
class IBMService:
    name: str
    guid: Optional[str]
    service_type: str        # service | integration_service | web_service | human_task
    description: Optional[str]
    inputs: list[dict] = field(default_factory=list)
    outputs: list[dict] = field(default_factory=list)
    steps: list[ServiceStep] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    source_path: str = ""
    tags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "guid": self.guid,
            "type": self.service_type,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "steps": [
                {
                    "id": s.step_id,
                    "name": s.name,
                    "type": s.step_type,
                    "script": s.script,
                    "called_service": s.called_service,
                    "inputs": s.inputs,
                    "outputs": s.outputs,
                    "condition": s.condition,
                    "error_handler": s.error_handler,
                }
                for s in self.steps
            ],
            "dependencies": self.dependencies,
            "tags": self.tags,
        }


class ServiceExtractor:
    """Extracts all services and their internal logic from a parsed TWX package."""

    def __init__(self, package: TWXPackage):
        self.package = package

    def extract(self) -> list[IBMService]:
        services: list[IBMService] = []

        type_map = {
            "service_is":    "Integration Service (IS)",
            "service_gss":   "General System Service (GSS)",
            "service_hhs":   "Human Service (HHS)",
            "service_other": "Service",
            "web_service":   "Web Service",
        }

        for artifact in self.package.artifacts:
            if artifact.artifact_type in type_map and artifact.tree:
                svc = self._parse_service(artifact, type_map[artifact.artifact_type])
                if svc:
                    services.append(svc)

        return services

    def extract_scripts(self) -> list[dict]:
        """Returns all JavaScript/server scripts found in any service step."""
        scripts = []
        service_types = {
            "service_is", "service_gss", "service_hhs", "service_other",
            "business_process", "web_service",
        }
        for artifact in self.package.artifacts:
            if artifact.artifact_type in service_types and artifact.tree:
                root = artifact.tree.getroot()
                for el in root.iter():
                    local = el.tag.split("}")[-1]
                    if local in ("script", "Script", "serverScript", "javascript"):
                        code = el.text or ""
                        if code.strip():
                            scripts.append({
                                "artifact": artifact.name,
                                "step_id": el.get("id", ""),
                                "step_name": el.get("name", ""),
                                "language": "JavaScript",
                                "code": code.strip(),
                            })
        return scripts

    def extract_sql_queries(self) -> list[dict]:
        """Finds all SQL queries embedded inside service steps."""
        queries = []
        for artifact in self.package.artifacts:
            if artifact.tree is None:
                continue
            root = artifact.tree.getroot()
            for el in root.iter():
                local = el.tag.split("}")[-1]
                if local in ("query", "sql", "sqlQuery", "queryText"):
                    sql = el.text or ""
                    if sql.strip():
                        queries.append({
                            "artifact": artifact.name,
                            "step_id": el.get("id", ""),
                            "sql": sql.strip(),
                        })
        return queries

    def extract_rest_endpoints(self) -> list[dict]:
        """Extracts REST/HTTP integration endpoints referenced in services."""
        endpoints = []
        for artifact in self.package.artifacts:
            if artifact.tree is None:
                continue
            root = artifact.tree.getroot()
            for el in root.iter():
                local = el.tag.split("}")[-1]
                if local in ("httpRequest", "restEndpoint", "externalService", "wsdlEndpoint", "url"):
                    url = el.get("url") or el.get("endpoint") or el.text or ""
                    if url.strip():
                        endpoints.append({
                            "artifact": artifact.name,
                            "type": local,
                            "url": url.strip(),
                            "method": el.get("method", ""),
                            "binding": el.get("binding", ""),
                        })
        return endpoints

    # ------------------------------------------------------------------ private

    def _parse_service(self, artifact: TWXArtifact, svc_type: str) -> Optional[IBMService]:
        root = artifact.tree.getroot()

        # IBM TWX structure: <teamworks><process name="..."> — get the child element
        child = next(iter(root), None)
        working_root = child if child is not None else root

        name = working_root.get("name") or artifact.name

        svc = IBMService(
            name=name,
            guid=artifact.guid,
            service_type=svc_type,
            description=artifact.description,
            source_path=artifact.path,
            tags=artifact.tags,
        )

        # Parameters (inputs / outputs)
        for el in working_root.iter():
            local = el.tag.split("}")[-1]
            if local in ("input", "inputMapping", "inputVar"):
                svc.inputs.append(self._param_dict(el))
            elif local in ("output", "outputMapping", "outputVar"):
                svc.outputs.append(self._param_dict(el))

        # Steps / flow nodes
        for el in working_root.iter():
            local = el.tag.split("}")[-1]
            step_type = SERVICE_STEP_TYPES.get(local)
            if step_type is None:
                continue

            step = ServiceStep(
                step_id=el.get("id", ""),
                name=el.get("name") or el.get("label") or local,
                step_type=step_type,
            )

            # Embedded script
            for child in el.iter():
                child_local = child.tag.split("}")[-1]
                if child_local in ("script", "Script", "serverScript") and child.text:
                    step.script = child.text.strip()
                elif child_local in ("serviceRef", "calledElement", "calledService"):
                    step.called_service = child.get("name") or child.get("ref") or child.text
                elif child_local in ("condition", "expression"):
                    step.condition = child.text

            # Input/output mappings within step
            for child in el:
                child_local = child.tag.split("}")[-1]
                if child_local == "input":
                    step.inputs.append(self._param_dict(child))
                elif child_local == "output":
                    step.outputs.append(self._param_dict(child))

            step.error_handler = el.get("isErrorHandler", "false").lower() == "true"
            svc.steps.append(step)

        # Dependencies (called services)
        svc.dependencies = list({
            s.called_service for s in svc.steps
            if s.called_service
        })

        return svc

    @staticmethod
    def _param_dict(el: ET.Element) -> dict:
        return {
            "name": el.get("name") or el.get("id", ""),
            "type": el.get("type") or el.get("typeRef") or el.get("dataType", "ANY"),
            "is_list": el.get("isList", "false").lower() == "true",
            "required": el.get("required", "false").lower() == "true",
            "description": next(
                (c.text.strip() for c in el if c.tag.split("}")[-1] == "description" and c.text),
                None,
            ),
        }
