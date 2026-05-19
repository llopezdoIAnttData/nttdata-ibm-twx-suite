"""Maps process flows, call graphs and inter-service dependencies from a TWXPackage."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
from .twx_parser import TWXPackage


@dataclass
class FlowNode:
    node_id: str
    name: str
    node_type: str
    artifact: str


@dataclass
class FlowEdge:
    source_id: str
    target_id: str
    label: Optional[str] = None
    condition: Optional[str] = None
    is_error_path: bool = False


@dataclass
class ProcessFlow:
    name: str
    guid: Optional[str]
    artifact_type: str
    nodes: list[FlowNode] = field(default_factory=list)
    edges: list[FlowEdge] = field(default_factory=list)
    source_path: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "guid": self.guid,
            "type": self.artifact_type,
            "nodes": [{"id": n.node_id, "name": n.name, "type": n.node_type} for n in self.nodes],
            "edges": [
                {
                    "from": e.source_id,
                    "to": e.target_id,
                    "label": e.label,
                    "condition": e.condition,
                    "error": e.is_error_path,
                }
                for e in self.edges
            ],
        }

    def to_mermaid(self) -> str:
        """Generates a Mermaid flowchart for this process."""
        lines = ["flowchart TD"]
        node_labels: dict[str, str] = {}

        for node in self.nodes:
            safe_id = _safe_id(node.node_id)
            label = node.name or node.node_id
            node_labels[node.node_id] = safe_id

            if node.node_type in ("Start", "startEvent"):
                lines.append(f'    {safe_id}(("{label}"))')
            elif node.node_type in ("End", "endEvent"):
                lines.append(f'    {safe_id}((("{label}")))')
            elif node.node_type in ("Gateway", "gatewayNode"):
                lines.append(f'    {safe_id}{{"{label}"}}')
            elif node.node_type in ("Script", "scriptTask"):
                lines.append(f'    {safe_id}[/"{label}"/]')
            else:
                lines.append(f'    {safe_id}["{label}"]')

        for edge in self.edges:
            src = node_labels.get(edge.source_id, _safe_id(edge.source_id))
            tgt = node_labels.get(edge.target_id, _safe_id(edge.target_id))
            arrow = "-->" if not edge.is_error_path else "-.->"
            if edge.label or edge.condition:
                lbl = edge.label or edge.condition or ""
                lines.append(f'    {src} {arrow}|"{lbl}"| {tgt}')
            else:
                lines.append(f"    {src} {arrow} {tgt}")

        return "\n".join(lines)


@dataclass
class DependencyGraph:
    """Call graph between all artifacts in the package."""
    nodes: list[str] = field(default_factory=list)
    edges: list[tuple[str, str, str]] = field(default_factory=list)  # (caller, callee, type)

    def to_mermaid(self) -> str:
        lines = ["graph LR"]
        seen_nodes = set()
        for node in self.nodes:
            safe = _safe_id(node)
            if safe not in seen_nodes:
                lines.append(f'    {safe}["{node}"]')
                seen_nodes.add(safe)
        for caller, callee, rel in self.edges:
            lines.append(f'    {_safe_id(caller)} -->|"{rel}"| {_safe_id(callee)}')
        return "\n".join(lines)


class FlowMapper:
    """Builds process flows and a full dependency graph from a parsed TWX package."""

    FLOW_TYPES = ("business_process", "service", "integration_service", "human_task")
    NODE_TAGS = {
        "startEvent", "endEvent", "scriptTask", "serviceTask", "systemTask",
        "userTask", "decisionTask", "integrationTask", "gatewayNode",
        "subProcess", "callActivity", "intermediateEvent",
    }
    EDGE_TAGS = {
        "sequenceFlow", "transition", "connection", "link", "flow",
    }

    def __init__(self, package: TWXPackage):
        self.package = package

    def extract_flows(self) -> list[ProcessFlow]:
        flows = []
        for artifact in self.package.artifacts:
            if artifact.artifact_type in self.FLOW_TYPES and artifact.tree:
                flow = self._parse_flow(artifact)
                flows.append(flow)
        return flows

    def build_dependency_graph(self) -> DependencyGraph:
        graph = DependencyGraph()
        name_set: set[str] = set()

        for artifact in self.package.artifacts:
            name_set.add(artifact.name)

        graph.nodes = sorted(name_set)

        for artifact in self.package.artifacts:
            if artifact.tree is None:
                continue
            root = artifact.tree.getroot()
            for el in root.iter():
                local = el.tag.split("}")[-1]
                if local in ("serviceRef", "calledElement", "calledService", "processRef"):
                    ref = el.get("name") or el.get("ref") or el.text or ""
                    ref = ref.strip()
                    if ref and ref != artifact.name:
                        edge = (artifact.name, ref, local)
                        if edge not in graph.edges:
                            graph.edges.append(edge)
                        if ref not in name_set:
                            graph.nodes.append(ref)
                            name_set.add(ref)

        return graph

    def find_entry_points(self) -> list[dict]:
        """Identifies processes/services that are not called by any other artifact."""
        all_names = {a.name for a in self.package.artifacts}
        called: set[str] = set()

        for artifact in self.package.artifacts:
            if artifact.tree is None:
                continue
            root = artifact.tree.getroot()
            for el in root.iter():
                local = el.tag.split("}")[-1]
                if local in ("serviceRef", "calledElement", "calledService", "processRef"):
                    ref = el.get("name") or el.get("ref") or el.text or ""
                    called.add(ref.strip())

        entry_points = []
        for artifact in self.package.artifacts:
            if artifact.name not in called:
                entry_points.append({
                    "name": artifact.name,
                    "type": artifact.artifact_type,
                    "path": artifact.path,
                })
        return entry_points

    # ------------------------------------------------------------------ private

    def _parse_flow(self, artifact) -> ProcessFlow:
        root = artifact.tree.getroot()
        flow = ProcessFlow(
            name=root.get("name") or root.get("id") or artifact.name,
            guid=artifact.guid,
            artifact_type=artifact.artifact_type,
            source_path=artifact.path,
        )

        for el in root.iter():
            local = el.tag.split("}")[-1]

            if local in self.NODE_TAGS:
                node = FlowNode(
                    node_id=el.get("id", f"node_{len(flow.nodes)}"),
                    name=el.get("name") or el.get("label") or local,
                    node_type=local,
                    artifact=artifact.name,
                )
                flow.nodes.append(node)

            elif local in self.EDGE_TAGS:
                source = el.get("sourceRef") or el.get("from") or el.get("source", "")
                target = el.get("targetRef") or el.get("to") or el.get("target", "")
                if source and target:
                    cond = None
                    for child in el:
                        if child.tag.split("}")[-1] in ("conditionExpression", "condition"):
                            cond = child.text
                    edge = FlowEdge(
                        source_id=source,
                        target_id=target,
                        label=el.get("name") or el.get("label"),
                        condition=cond,
                        is_error_path=el.get("isDefault", "false") == "false"
                        and "error" in (el.get("name") or "").lower(),
                    )
                    flow.edges.append(edge)

        return flow


def _safe_id(raw: str) -> str:
    """Converts a GUID or name to a valid Mermaid node identifier."""
    return "N" + "".join(c if c.isalnum() else "_" for c in raw)[:40]
