"""Generates Markdown documentation from extracted TWX artifacts."""

from datetime import datetime
from typing import Optional
from .twx_parser import TWXPackage
from .entity_extractor import EntityExtractor, BusinessObject
from .service_extractor import ServiceExtractor, IBMService
from .flow_mapper import FlowMapper, ProcessFlow


NTTDATA_HEADER = """<!--
  NTTDATA IBM TWX Reverse Engineering Suite
  Generated: {date}
  Version:   {version}
  Corporate: NTTDATA
-->
"""


class DocGenerator:
    """Produces full Markdown documentation for a TWX package."""

    def __init__(self, package: TWXPackage, version: str = "1.0.0"):
        self.package = package
        self.version = version
        self.entity_extractor = EntityExtractor(package)
        self.service_extractor = ServiceExtractor(package)
        self.flow_mapper = FlowMapper(package)

    def generate_full(self) -> str:
        entities  = self.entity_extractor.extract()
        variables = self.entity_extractor.extract_variables()
        services  = self.service_extractor.extract()
        scripts   = self.service_extractor.extract_scripts()
        endpoints = self.service_extractor.extract_rest_endpoints()
        flows     = self.flow_mapper.extract_flows()
        dep_graph = self.flow_mapper.build_dependency_graph()
        entries   = self.flow_mapper.find_entry_points()

        sections = [
            NTTDATA_HEADER.format(date=datetime.now().strftime("%Y-%m-%d %H:%M"), version=self.version),
            self._section_summary(),
            self._section_entities(entities),
            self._section_services(services),
            self._section_scripts(scripts),
            self._section_endpoints(endpoints),
            self._section_flows(flows),
            self._section_dependency_graph(dep_graph),
            self._section_entry_points(entries),
            self._section_variables(variables),
        ]
        return "\n\n".join(s for s in sections if s.strip())

    def generate_summary(self) -> str:
        return self._section_summary()

    def generate_entities_doc(self) -> str:
        entities = self.entity_extractor.extract()
        return "\n\n".join([
            NTTDATA_HEADER.format(date=datetime.now().strftime("%Y-%m-%d %H:%M"), version=self.version),
            self._section_entities(entities),
        ])

    def generate_services_doc(self) -> str:
        services = self.service_extractor.extract()
        return "\n\n".join([
            NTTDATA_HEADER.format(date=datetime.now().strftime("%Y-%m-%d %H:%M"), version=self.version),
            self._section_services(services),
        ])

    def generate_flows_doc(self) -> str:
        flows = self.flow_mapper.extract_flows()
        return "\n\n".join([
            NTTDATA_HEADER.format(date=datetime.now().strftime("%Y-%m-%d %H:%M"), version=self.version),
            self._section_flows(flows),
        ])

    # ------------------------------------------------------------------ sections

    def _section_summary(self) -> str:
        s = self.package.summary
        lines = [
            f"# {s['app_name']} — Reverse Engineering Report",
            "",
            f"| Campo          | Valor |",
            f"|:---------------|:------|",
            f"| Aplicación     | `{s['app_name']}` |",
            f"| Versión TWX    | `{s['app_version']}` |",
            f"| Toolkit        | `{'Sí' if s['toolkit'] else 'No'}` |",
            f"| Total artefactos | **{s['total_artifacts']}** |",
            "",
            "## Artefactos por tipo",
            "",
            "| Tipo | Cantidad |",
            "|:-----|:---------|",
        ]
        for atype, count in sorted(s["by_type"].items()):
            lines.append(f"| {atype.replace('_', ' ').title()} | {count} |")
        return "\n".join(lines)

    def _section_entities(self, entities: list[BusinessObject]) -> str:
        if not entities:
            return ""
        lines = ["## Business Objects / Entidades", ""]
        for bo in entities:
            lines.append(f"### `{bo.name}`")
            if bo.description:
                lines.append(f"> {bo.description}")
            if bo.parent:
                lines.append(f"\n**Hereda de:** `{bo.parent}`")
            if bo.namespace:
                lines.append(f"\n**Namespace:** `{bo.namespace}`")
            if bo.fields:
                lines += [
                    "",
                    "| Campo | Tipo | Lista | Requerido | Descripción |",
                    "|:------|:-----|:-----:|:---------:|:------------|",
                ]
                for f in bo.fields:
                    req  = "✓" if f.required else ""
                    lst  = "✓" if f.is_list  else ""
                    desc = f.description or ""
                    lines.append(f"| `{f.name}` | `{f.type_ref}` | {lst} | {req} | {desc} |")
            lines.append("")
        return "\n".join(lines)

    def _section_services(self, services: list[IBMService]) -> str:
        if not services:
            return ""
        lines = ["## Servicios", ""]
        for svc in services:
            lines.append(f"### `{svc.name}` _{svc.service_type}_")
            if svc.description:
                lines.append(f"> {svc.description}")
            if svc.inputs:
                lines += ["", "**Inputs:**", ""]
                lines += self._param_table(svc.inputs)
            if svc.outputs:
                lines += ["", "**Outputs:**", ""]
                lines += self._param_table(svc.outputs)
            if svc.steps:
                lines += ["", f"**Pasos ({len(svc.steps)}):**", ""]
                lines += [
                    "| # | Nombre | Tipo | Servicio llamado |",
                    "|:-:|:-------|:-----|:----------------|",
                ]
                for i, step in enumerate(svc.steps, 1):
                    called = f"`{step.called_service}`" if step.called_service else "—"
                    lines.append(f"| {i} | {step.name} | {step.step_type} | {called} |")
            if svc.dependencies:
                lines.append(f"\n**Dependencias:** " + ", ".join(f"`{d}`" for d in svc.dependencies))
            lines.append("")
        return "\n".join(lines)

    def _section_scripts(self, scripts: list[dict]) -> str:
        if not scripts:
            return ""
        lines = ["## Scripts embebidos", ""]
        for script in scripts:
            lines.append(f"### `{script['artifact']}` — {script.get('step_name') or script.get('step_id', '')}")
            lines += [
                f"```javascript",
                script["code"],
                "```",
                "",
            ]
        return "\n".join(lines)

    def _section_endpoints(self, endpoints: list[dict]) -> str:
        if not endpoints:
            return ""
        lines = [
            "## Endpoints externos / Integraciones",
            "",
            "| Artefacto | Tipo | Método | URL |",
            "|:----------|:-----|:------:|:----|",
        ]
        for ep in endpoints:
            lines.append(f"| `{ep['artifact']}` | {ep['type']} | {ep.get('method','') or '—'} | `{ep['url']}` |")
        return "\n".join(lines)

    def _section_flows(self, flows: list[ProcessFlow]) -> str:
        if not flows:
            return ""
        lines = ["## Diagramas de flujo", ""]
        for flow in flows:
            if not flow.nodes:
                continue
            lines.append(f"### {flow.name}")
            lines += [
                "",
                "```mermaid",
                flow.to_mermaid(),
                "```",
                "",
            ]
        return "\n".join(lines)

    def _section_dependency_graph(self, dep_graph) -> str:
        if not dep_graph.edges:
            return ""
        lines = [
            "## Grafo de dependencias",
            "",
            "```mermaid",
            dep_graph.to_mermaid(),
            "```",
            "",
        ]
        return "\n".join(lines)

    def _section_entry_points(self, entries: list[dict]) -> str:
        if not entries:
            return ""
        lines = [
            "## Puntos de entrada (Entry Points)",
            "",
            "Artefactos que no son invocados por ningún otro dentro del paquete:",
            "",
            "| Nombre | Tipo |",
            "|:-------|:-----|",
        ]
        for ep in entries:
            lines.append(f"| `{ep['name']}` | {ep['type'].replace('_', ' ').title()} |")
        return "\n".join(lines)

    def _section_variables(self, variables: list[dict]) -> str:
        if not variables:
            return ""
        lines = [
            "## Variables globales / Parámetros",
            "",
            "| Artefacto | Variable | Tipo | In | Out | Lista |",
            "|:----------|:---------|:-----|:--:|:---:|:-----:|",
        ]
        for v in variables:
            inp = "✓" if v.get("is_input") else ""
            out = "✓" if v.get("is_output") else ""
            lst = "✓" if v.get("is_list") else ""
            lines.append(
                f"| `{v['artifact']}` | `{v['name']}` | `{v['type']}` | {inp} | {out} | {lst} |"
            )
        return "\n".join(lines)

    @staticmethod
    def _param_table(params: list[dict]) -> list[str]:
        rows = [
            "| Nombre | Tipo | Lista | Requerido |",
            "|:-------|:-----|:-----:|:---------:|",
        ]
        for p in params:
            lst = "✓" if p.get("is_list") else ""
            req = "✓" if p.get("required") else ""
            rows.append(f"| `{p['name']}` | `{p['type']}` | {lst} | {req} |")
        return rows
