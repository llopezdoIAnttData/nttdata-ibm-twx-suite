"""F3 Parametría Extractor — Ciclo 10.

Analiza un TWXPackage y produce el mapeo de arquitectura F3:

1. Clasifica cada BO en: domain_entity | dto | catalog
2. Detecta "puntos de corte F3" en cada BPD (donde un IS async espera UCA)
3. Genera la tabla de parametría (step → condiciones → siguiente proceso F3)
4. Lista los campos que deben ir a NOV_INSTANCE_MANAGEMENT

Uso:
    from ibm_twx_tools.parametria_extractor import ParametriaExtractor
    report = ParametriaExtractor(package).extract()
    print(report.to_json())
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Optional

from .twx_parser import TWXPackage
from .entity_extractor import EntityExtractor, BusinessObject
from .service_extractor import ServiceExtractor


# ─────────────────────────────────────────────────────────────────────────────
# BO Classification
# ─────────────────────────────────────────────────────────────────────────────

CATALOG_KEYWORDS = {
    "catalogo", "catalog", "tipo", "estatus", "status", "siefore",
    "subcuenta", "subcta", "origen", "regimen", "grupo", "banco",
}
DOMAIN_ENTITY_FIELDS = {"identificador", "folio", "foliosubsecuente", "idarchivo"}
# IBM BPM variable prefixes that indicate cross-step state
GATEWAY_VAR_PATTERN = re.compile(
    r"tw\.local\.(salida|exitoso|esAcreditacion|finalizarFlujo|existeNoRechazados|"
    r"rechazarFolio|opcionIDC|opcionIdc|folioSubSecuente|folio|idInstancia|"
    r"idProceso|idSubproceso|idSubetapa|resultado|continuar|accion)",
    re.IGNORECASE,
)


def classify_bo(bo: BusinessObject, uca_bo_names: set[str]) -> str:
    """Classify a BO into domain_entity | catalog | dto."""
    name_lower = bo.name.lower()

    # Catalog: name contains catalog keywords and has few fields (id + description)
    if any(kw in name_lower for kw in CATALOG_KEYWORDS):
        return "catalog"

    # Domain Entity: referenced in UCAs, or has folio/identificador field
    if bo.name in uca_bo_names:
        return "domain_entity"
    field_names_lower = {f.name.lower() for f in bo.fields}
    if field_names_lower & DOMAIN_ENTITY_FIELDS:
        return "domain_entity"
    if len(bo.fields) > 10:  # Large BOs with many fields are usually domain entities
        return "domain_entity"

    return "dto"


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class F3Step:
    """One ephemeral process in F3 (lanzador o respuesta-bus)."""
    step_id: int
    appian_process_name: str
    step_role: str          # "launcher" | "respuesta_bus" | "error"
    ibm_is_name: str        # IBM Integration Service that triggers this step
    ibm_uca_name: str       # IBM UCA that resumes after this step
    decision_vars: list[str]
    exits: list[dict]       # [{"condition": ..., "next_step_id": ..., "next_process": ...}]


@dataclass
class F3BPDDecomposition:
    """F3 decomposition of one IBM BPD."""
    bpd_name: str
    async_point_count: int
    steps: list[F3Step]
    nov_respuesta_bus_name: str


@dataclass
class NOVInstanceField:
    """A variable that must persist in NOV_INSTANCE_MANAGEMENT between F3 steps."""
    campo_ibm: str
    campo_appian: str
    tipo_appian: str
    motivo: str


@dataclass
class BOCategory:
    bo_name: str
    category: str           # domain_entity | dto | catalog
    appian_target: str      # Record Type | CDT | skip
    field_count: int
    justification: str


@dataclass
class F3ParametriaReport:
    """Complete F3 architecture mapping for a TWX package."""
    twx_name: str
    bo_categories: list[BOCategory]
    bpd_decompositions: list[F3BPDDecomposition]
    nov_instance_fields: list[NOVInstanceField]

    def to_dict(self) -> dict:
        return {
            "twx_name": self.twx_name,
            "bo_categories": [
                {
                    "bo_name": c.bo_name,
                    "category": c.category,
                    "appian_target": c.appian_target,
                    "field_count": c.field_count,
                    "justification": c.justification,
                }
                for c in self.bo_categories
            ],
            "bpd_decompositions": [
                {
                    "bpd_name": d.bpd_name,
                    "async_point_count": d.async_point_count,
                    "nov_respuesta_bus_name": d.nov_respuesta_bus_name,
                    "steps": [
                        {
                            "step_id": s.step_id,
                            "appian_process_name": s.appian_process_name,
                            "step_role": s.step_role,
                            "ibm_is_name": s.ibm_is_name,
                            "ibm_uca_name": s.ibm_uca_name,
                            "decision_vars": s.decision_vars,
                            "exits": s.exits,
                        }
                        for s in d.steps
                    ],
                }
                for d in self.bpd_decompositions
            ],
            "nov_instance_management_fields": [
                {
                    "campo_ibm": f.campo_ibm,
                    "campo_appian": f.campo_appian,
                    "tipo_appian": f.tipo_appian,
                    "motivo": f.motivo,
                }
                for f in self.nov_instance_fields
            ],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_summary(self) -> str:
        lines = [
            f"=== F3 Parametría Report: {self.twx_name} ===\n",
            f"Business Objects clasificados: {len(self.bo_categories)}",
        ]
        counts = {"domain_entity": 0, "dto": 0, "catalog": 0}
        for c in self.bo_categories:
            counts[c.category] = counts.get(c.category, 0) + 1
        for cat, cnt in counts.items():
            lines.append(f"  {cat}: {cnt}")

        lines.append(f"\nBPDs descompuestos en F3: {len(self.bpd_decompositions)}")
        for d in self.bpd_decompositions:
            lines.append(f"  {d.bpd_name}: {d.async_point_count} puntos async → {len(d.steps)} procesos efímeros")

        lines.append(f"\nCampos NOV_INSTANCE_MANAGEMENT: {len(self.nov_instance_fields)}")
        for f in self.nov_instance_fields:
            lines.append(f"  {f.campo_ibm} -> {f.campo_appian} ({f.tipo_appian})")

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Extractor
# ─────────────────────────────────────────────────────────────────────────────

class ParametriaExtractor:
    """Extracts F3 architecture mapping from a parsed TWX package."""

    # Known IBM variable → Appian field mappings (from SKILL.md v3)
    KNOWN_VAR_MAP = {
        "tw.local.salida":             ("ACTION_OUT",          "Integer"),
        "tw.local.exitoso":            ("STATUS_ID",           "Boolean"),
        "tw.local.folio":              ("FOLIO",               "Text"),
        "tw.local.folioSubSecuente":   ("FOLIO_SUBSECUENTE",   "Text"),
        "tw.local.esAcreditacion":     ("ES_ACREDITACION",     "Boolean"),
        "tw.local.finalizarFlujo":     ("FINALIZAR_FLUJO",     "Boolean"),
        "tw.local.existeNoRechazados": ("EXISTE_NO_RECHAZADOS","Boolean"),
        "tw.local.rechazarFolio":      ("RECHAZAR_FOLIO",      "Boolean"),
        "tw.local.opcionIDC":          ("ACCION_IDC",          "Text"),
        "tw.local.opcionIdc":          ("ACCION_IDC",          "Text"),
        "tw.local.idInstancia":        ("ID_INSTANCIA",        "Integer"),
        "tw.local.resultado":          ("RESULTADO",           "Text"),
        "tw.local.continuar":          ("CONTINUAR",           "Boolean"),
        "tw.local.accion":             ("ACCION",              "Text"),
    }

    def __init__(self, package: TWXPackage):
        self.package = package

    def extract(self) -> F3ParametriaReport:
        twx_name = self.package.app_name or "TWX"

        # 1. Extract all UCAs to find which BOs they reference (for domain_entity detection)
        uca_bo_names = self._get_uca_referenced_bos()

        # 2. Classify BOs
        entity_extractor = EntityExtractor(self.package)
        bos = entity_extractor.extract()
        bo_categories = [self._classify_bo(bo, uca_bo_names) for bo in bos]

        # 3. Extract all gateway scripts to find cross-step variables
        gateway_vars = self._extract_gateway_vars()

        # 4. Build F3 decomposition for each BPD
        decompositions = self._build_f3_decompositions(gateway_vars)

        # 5. Build NOV_INSTANCE_MANAGEMENT field list from gateway vars
        nov_fields = self._build_nov_instance_fields(gateway_vars)

        return F3ParametriaReport(
            twx_name=twx_name,
            bo_categories=bo_categories,
            bpd_decompositions=decompositions,
            nov_instance_fields=nov_fields,
        )

    # ─────────────────────────────────────────────── private

    def _get_uca_referenced_bos(self) -> set[str]:
        """Find BO names referenced in UCA correlation or event definitions."""
        uca_bo_names: set[str] = set()
        for artifact in self.package.artifacts:
            if artifact.artifact_type != "event_handler" or not artifact.tree:
                continue
            root = artifact.tree.getroot()
            for el in root.iter():
                local = el.tag.split("}")[-1]
                if local in ("correlationData", "schedEvent", "eventSubscription"):
                    type_ref = el.get("type") or el.get("typeRef") or el.get("dataType", "")
                    if type_ref:
                        uca_bo_names.add(type_ref.split(".")[-1])
                    for child in el:
                        child_type = child.get("type") or child.get("typeRef") or ""
                        if child_type:
                            uca_bo_names.add(child_type.split(".")[-1])
        return uca_bo_names

    def _classify_bo(self, bo: BusinessObject, uca_bo_names: set[str]) -> BOCategory:
        category = classify_bo(bo, uca_bo_names)
        if category == "domain_entity":
            target = "Record Type (tabla NOV_*)"
            field_names = {f.name.lower() for f in bo.fields}
            if field_names & DOMAIN_ENTITY_FIELDS:
                justification = f"Tiene campo de identidad ({', '.join(field_names & DOMAIN_ENTITY_FIELDS)})"
            elif bo.name in uca_bo_names:
                justification = "Referenciado en correlación de UCA"
            else:
                justification = f"BO de dominio amplio ({len(bo.fields)} campos)"
        elif category == "catalog":
            target = "skip (tabla catálogo existente o Constant)"
            justification = "Nombre indica dato de referencia (catálogo/tipo/estatus)"
        else:
            target = "CDT / variable de proceso local"
            justification = "Solo vive dentro de un paso (request/response de IS)"

        return BOCategory(
            bo_name=bo.name,
            category=category,
            appian_target=target,
            field_count=len(bo.fields),
            justification=justification,
        )

    def _extract_gateway_vars(self) -> set[str]:
        """Extract tw.local.* variables used in gateways across all services and BPDs."""
        found_vars: set[str] = set()
        extractor = ServiceExtractor(self.package)
        scripts = extractor.extract_scripts()
        for script in scripts:
            code = script.get("code", "") or ""
            for match in GATEWAY_VAR_PATTERN.finditer(code):
                found_vars.add(match.group(0))  # preserve case for KNOWN_VAR_MAP lookup
        return found_vars

    def _get_uca_name_map(self) -> dict[str, str]:
        """Build UCA ID -> name map from all UCA artifacts in the package."""
        uca_map: dict[str, str] = {}
        for artifact in self.package.artifacts:
            if artifact.artifact_type != "uca" or not artifact.tree:
                continue
            root = artifact.tree.getroot()
            for child in root:
                uca_id = child.get("id", "")
                uca_name = child.get("name", "") or artifact.name
                if uca_id and uca_name:
                    uca_map[uca_id] = uca_name
                    # Also index without namespace prefix (e.g. "pkg-guid/4.xxx" -> "4.xxx")
                    local_id = uca_id.split("/")[-1] if "/" in uca_id else uca_id
                    uca_map[local_id] = uca_name
        return uca_map

    def _build_f3_decompositions(self, gateway_vars: set[str]) -> list[F3BPDDecomposition]:
        """Build F3 ephemeral process decomposition for each BPD.

        Parses BPD XML directly (IBM BPM uses <flowObject> not BPMN standard tags).
        """
        decompositions: list[F3BPDDecomposition] = []
        uca_name_map = self._get_uca_name_map()

        for artifact in self.package.by_type("business_process"):
            if not artifact.tree:
                continue

            bpd_name = artifact.name or "BPD"
            async_points = self._detect_async_points_ibm(artifact, uca_name_map)
            n_async = len(async_points)

            bpd_name_clean = bpd_name.replace(" ", "").replace("-", "")
            nov_bus_name = f"NOV Respuesta Bus {bpd_name}"

            steps: list[F3Step] = []
            for i, ap in enumerate(async_points):
                step_id = i + 1
                is_name = ap.get("is_name", "IS Desconocido")
                uca_name = ap.get("uca_name", "UCA Desconocido")
                process_name = f"NOV {bpd_name_clean} Paso{step_id}"
                step_vars = list(gateway_vars)

                exits = [
                    {
                        "condicion": "STATUS_ID=true AND ACTION_OUT=0",
                        "siguiente_paso": step_id + 1,
                        "siguiente_proceso": (
                            f"NOV {bpd_name_clean} Paso{step_id + 1}"
                            if i < n_async - 1
                            else f"NOV {bpd_name_clean} Finalizar"
                        ),
                    },
                    {
                        "condicion": "STATUS_ID=false",
                        "siguiente_paso": -1,
                        "siguiente_proceso": f"NOV {bpd_name_clean} Error",
                    },
                ]

                steps.append(F3Step(
                    step_id=step_id,
                    appian_process_name=process_name,
                    step_role="launcher",
                    ibm_is_name=is_name,
                    ibm_uca_name=uca_name,
                    decision_vars=step_vars,
                    exits=exits,
                ))

            # Add final "Finalizar" step for BPDs with async points
            if n_async > 0:
                steps.append(F3Step(
                    step_id=n_async + 1,
                    appian_process_name=f"NOV {bpd_name_clean} Finalizar",
                    step_role="launcher",
                    ibm_is_name="(ninguno - cierre de flujo)",
                    ibm_uca_name="(ninguno)",
                    decision_vars=[],
                    exits=[],
                ))

            decompositions.append(F3BPDDecomposition(
                bpd_name=bpd_name,
                async_point_count=n_async,
                steps=steps,
                nov_respuesta_bus_name=nov_bus_name,
            ))

        return decompositions

    def _detect_async_points_ibm(self, artifact, uca_name_map: dict[str, str]) -> list[dict]:
        """
        Detect async break points directly from IBM BPM TWX BPD XML.

        IBM BPM BPDs use <flowObject componentType="Event"> with <eventType>1</eventType>
        and <attachedUcaId> to represent UCA wait points (async breaks). This is different
        from BPMN standard <intermediateEvent> used in FlowMapper.

        Also collects the IS activity name that precedes each UCA wait by looking at
        <flowObject componentType="Activity"> with IS service references (<attachedActivityId>
        containing '/1.' or starting with '/1.').
        """
        root = artifact.tree.getroot()
        async_points: list[dict] = []

        # Collect all IS activity names (activities that call integration services)
        is_activity_names: list[str] = []
        for el in root.iter():
            if el.tag.split("}")[-1] != "flowObject":
                continue
            if el.get("componentType") != "Activity":
                continue
            fo_name = ""
            has_is_ref = False
            for child in el:
                cl = child.tag.split("}")[-1]
                if cl == "name" and child.text:
                    fo_name = child.text.strip()
            for sub in el.iter():
                sl = sub.tag.split("}")[-1]
                if sl == "attachedActivityId" and sub.text:
                    ref = sub.text.strip()
                    # Local IS reference: starts with /1. or contains /1.
                    if ref.startswith("/1.") or (ref.count("/") == 1 and "/1." in ref):
                        has_is_ref = True
                        break
            if has_is_ref and fo_name:
                is_activity_names.append(fo_name)

        # Find UCA wait events: flowObject[componentType=Event] with eventType=1 + attachedUcaId
        uca_idx = 0
        for el in root.iter():
            if el.tag.split("}")[-1] != "flowObject":
                continue
            if el.get("componentType") != "Event":
                continue

            event_type = None
            uca_id = None

            for sub in el.iter():
                sl = sub.tag.split("}")[-1]
                if sl == "attachedUcaId" and sub.text and uca_id is None:
                    uca_id = sub.text.strip()
                    break  # found it, no need to continue iterating

            # Definitive identifier of a UCA wait = presence of attachedUcaId
            # (outer eventType varies: 1 in main BPDs, 3 in sub-process BPDs)
            if uca_id:
                # Normalize UCA ID: strip namespace prefix
                local_uca_id = uca_id.split("/")[-1] if "/" in uca_id else uca_id
                uca_name = uca_name_map.get(local_uca_id) or uca_name_map.get(uca_id) or uca_id

                # Pair with IS activity (best-effort: use positional match)
                is_name = is_activity_names[uca_idx] if uca_idx < len(is_activity_names) else "IG (IS asincrono)"

                async_points.append({
                    "uca_id": uca_id,
                    "uca_name": uca_name,
                    "is_name": is_name,
                })
                uca_idx += 1

        return async_points

    def _build_nov_instance_fields(self, gateway_vars: set[str]) -> list[NOVInstanceField]:
        """Build NOV_INSTANCE_MANAGEMENT field list from cross-step gateway variables."""
        # Build a lowercased index for case-insensitive lookup
        known_lower: dict[str, tuple[str, str]] = {
            k.lower(): v for k, v in self.KNOWN_VAR_MAP.items()
        }

        fields: list[NOVInstanceField] = []
        seen_lower: set[str] = set()  # deduplicate case variants

        for var in sorted(gateway_vars, key=str.lower):
            var_lower = var.lower()
            if var_lower in seen_lower:
                continue
            seen_lower.add(var_lower)

            mapping = self.KNOWN_VAR_MAP.get(var) or known_lower.get(var_lower)
            if mapping:
                campo_appian, tipo = mapping
                motivo = "Variable de decisión usada en gateway post-async"
            else:
                var_name = var.replace("tw.local.", "").replace("tw.Local.", "")
                campo_appian = re.sub(r"(?<!^)(?=[A-Z])", "_", var_name).upper()
                tipo = "Text"
                motivo = "Variable detectada en scripts de gateway"

            fields.append(NOVInstanceField(
                campo_ibm=var,
                campo_appian=campo_appian,
                tipo_appian=tipo,
                motivo=motivo,
            ))

        return fields
