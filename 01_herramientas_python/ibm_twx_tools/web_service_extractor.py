"""
Extracts WebService (prefix 7.*) artifacts and resolves their operation parameters
from the referenced IS processes (prefix 1.*).

Each IBM BPM WebService (SOAP) is a named endpoint that exposes one or more
operations. Each operation has a processRef pointing to an IS/GSS process.
The IS process holds the processParameter elements (INPUT=1 / OUTPUT=2).

Async Tipo 2 detection:
  A process exposed as a webServiceOperation is a callback receiver — it means
  an upstream sub-process sent an async request and is waiting for this callback
  to arrive. These are classified as "Async Tipo 2" (NOV_INSTANCE_MANAGEMENT pattern).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional

from .twx_parser import TWXPackage, TWXArtifact


# ── BPD variable names already covered by NCI_BR table ───────────────────────
_NCI_BR_COVERED: frozenset[str] = frozenset({
    "folio", "archivo", "idarchivo", "idproceso", "idproceso",
    "idsubproceso", "idsubproceso", "idsubetapa", "idetapa",
    "esproceso", "esreproceso", "esenvio", "exitocargo", "ismocargo",
    "exitoabono", "descproceso", "descsubproceso", "usuario",
})


@dataclass
class BPDVarInfo:
    name: str
    direction: str      # "IN" | "OUT" | "IN/OUT"
    is_array: bool
    type_name: str      # resolved or raw classId suffix
    frequency: int      # how many BPDs use this variable
    bpd_names: list[str] = field(default_factory=list)
    in_nci_br: bool = False


class BPDVariableExtractor:
    """Extracts BPD process variables (bpdParameter) from all BPD artifacts (prefix 25.*)."""

    def __init__(self, package: TWXPackage):
        self.package = package
        self._bo_names: dict[str, str] = {}
        for art in package.artifacts:
            if art.artifact_type == "business_object" and art.guid:
                self._bo_names[art.guid] = art.name
                short = art.guid.replace("12.", "") if art.guid.startswith("12.") else art.guid
                self._bo_names[short] = art.name

    def extract(self) -> list[BPDVarInfo]:
        """Returns unique BPD variables sorted by frequency descending."""
        # name (lowercase) → accumulated data
        agg: dict[str, dict] = {}

        for art in self.package.artifacts:
            if art.artifact_type != "business_process" or not art.tree:
                continue
            root = art.tree.getroot()
            bpd_el = next(iter(root), None)
            if bpd_el is None:
                continue
            bpd_name = bpd_el.get("name", art.name)

            for param_el in bpd_el.findall("bpdParameter"):
                var_name = param_el.get("name", "")
                if not var_name or var_name == "Untitled1":
                    continue
                ptype = param_el.findtext("parameterType") or "0"
                is_array = (param_el.findtext("isArrayOf") or "false").lower() == "true"
                class_id = param_el.findtext("classId") or ""
                type_name = self._resolve_type(class_id)
                direction = "IN" if ptype == "1" else ("OUT" if ptype == "2" else "?")

                key = var_name.lower()
                if key not in agg:
                    agg[key] = {
                        "name": var_name,
                        "directions": set(),
                        "is_array": is_array,
                        "type_name": type_name,
                        "count": 0,
                        "bpds": [],
                    }
                agg[key]["directions"].add(direction)
                agg[key]["count"] += 1
                if bpd_name not in agg[key]["bpds"]:
                    agg[key]["bpds"].append(bpd_name)

        result = []
        for key, data in agg.items():
            dirs = data["directions"]
            if "IN" in dirs and "OUT" in dirs:
                direction = "IN/OUT"
            elif "IN" in dirs:
                direction = "IN"
            else:
                direction = "OUT"
            result.append(BPDVarInfo(
                name=data["name"],
                direction=direction,
                is_array=data["is_array"],
                type_name=data["type_name"],
                frequency=data["count"],
                bpd_names=data["bpds"],
                in_nci_br=(key in _NCI_BR_COVERED),
            ))

        result.sort(key=lambda v: (-v.frequency, v.name))
        return result

    def _resolve_type(self, class_id: str) -> str:
        if not class_id:
            return "ANY"
        bo_part = class_id.rsplit("/", 1)[-1] if "/" in class_id else class_id
        if bo_part in self._bo_names:
            return self._bo_names[bo_part]
        _PRIM = {
            "12.83ff975e-8dbc-42e5-b738-fa8bc08274a2": "String",
            "12.db884a3c-c533-44b7-bb2d-47bec8ad4022": "String",
            "12.68474ab0-d56f-47ee-b7e9-510b45a2a8be": "String",
            "12.c09c9b6e-aabd-4897-bef2-ed61db106297": "Integer",
            "12.83ff975e-8dbc-42e5-b738-fa8bc08274a2": "Boolean",
        }
        if bo_part in _PRIM:
            return _PRIM[bo_part]
        # Check if the full classId starts with a known IBM type GUID
        _IBM = {
            "7f4f17d6-74fa-4f89-a8e3-f69d5b0fa787": "String",
            "7f4f17d6-74fa-4f89-a8e3-f69d5b0fa786": "Integer",
            "7f4f17d6-74fa-4f89-a8e3-f69d5b0fa785": "Decimal",
            "7f4f17d6-74fa-4f89-a8e3-f69d5b0fa784": "Boolean",
            "7f4f17d6-74fa-4f89-a8e3-f69d5b0fa783": "Date",
        }
        for guid, tname in _IBM.items():
            if class_id.startswith(guid):
                return tname
        return bo_part.split(".")[-1][:12] if bo_part else "ANY"


# ── Primitive type map: well-known classId prefixes → human-readable name ────
_KNOWN_TYPES: dict[str, str] = {
    "7f4f17d6-74fa-4f89-a8e3-f69d5b0fa787": "String",        # IBM String
    "7f4f17d6-74fa-4f89-a8e3-f69d5b0fa786": "Integer",
    "7f4f17d6-74fa-4f89-a8e3-f69d5b0fa785": "Decimal",
    "7f4f17d6-74fa-4f89-a8e3-f69d5b0fa784": "Boolean",
    "7f4f17d6-74fa-4f89-a8e3-f69d5b0fa783": "Date",
    "7f4f17d6-74fa-4f89-a8e3-f69d5b0fa782": "DateTime",
}
_PRIMITIVE_GUIDS = {
    "12.83ff975e-8dbc-42e5-b738-fa8bc08274a2": "String",
    "12.db884a3c-c533-44b7-bb2d-47bec8ad4022": "String",
    "12.68474ab0-d56f-47ee-b7e9-510b45a2a8be": "String",
}


@dataclass
class ParamInfo:
    name: str
    param_type: int     # 1 = INPUT, 2 = OUTPUT
    is_array: bool
    class_id: str       # raw classId value
    type_name: str      # resolved human-readable type
    raw_xml: str        # original processParameter XML fragment


@dataclass
class OperationInfo:
    name: str
    process_name: str
    inputs: list[ParamInfo] = field(default_factory=list)
    outputs: list[ParamInfo] = field(default_factory=list)
    is_async_tipo2: bool = False


@dataclass
class WSInfo:
    name: str
    binding: str            # soap12 | soap11 | rest
    operations: list[OperationInfo] = field(default_factory=list)


class WebServiceExtractor:
    """Parses all web_service (7.*) artifacts and resolves operation parameters."""

    def __init__(self, package: TWXPackage):
        self.package = package
        # Build lookup: artifact path suffix → artifact  e.g. "1.abc..." → artifact
        self._by_id: dict[str, TWXArtifact] = {}
        for art in package.artifacts:
            # path = "objects/1.xxx.xml" → key = "1.xxx"
            stem = art.path.replace("objects/", "").replace(".xml", "")
            self._by_id[stem] = art
            # Also index by short id without prefix, for flexibility
            if "." in stem:
                self._by_id[stem.split(".", 1)[1]] = art

        # Build BO GUID → name lookup from business_object artifacts
        self._bo_names: dict[str, str] = {}
        for art in package.artifacts:
            if art.artifact_type == "business_object" and art.tree and art.guid:
                # guid is like "12.abc..." strip prefix
                short = art.guid.replace("12.", "") if art.guid.startswith("12.") else art.guid
                self._bo_names[art.guid] = art.name
                self._bo_names[short] = art.name
                # full path key
                self._bo_names[art.path.replace("objects/", "").replace(".xml", "")] = art.name

    def extract(self) -> list[WSInfo]:
        result: list[WSInfo] = []
        for art in self.package.artifacts:
            if art.artifact_type == "web_service" and art.tree:
                ws = self._parse_ws(art)
                if ws:
                    result.append(ws)
        return result

    def extract_async_tipo2_names(self, ws_list: list[WSInfo]) -> list[str]:
        """
        Returns process names that are Async Tipo 2.
        Heuristic: any IS process referenced by a webServiceOperation is a callback
        receiver → async. We return the process name as displayed in the async grid.
        """
        async_names: list[str] = []
        for ws in ws_list:
            for op in ws.operations:
                if op.process_name:
                    async_names.append(op.process_name)
        return async_names

    # ── private ───────────────────────────────────────────────────────────────

    def _parse_ws(self, art: TWXArtifact) -> Optional[WSInfo]:
        root = art.tree.getroot()
        ws_el = next(iter(root), None)
        if ws_el is None:
            return None

        name = ws_el.get("name", art.name)
        binding = ws_el.findtext("bindingStyle") or "soap12"

        ws = WSInfo(name=name, binding=binding)

        for op_el in ws_el.findall("webServiceOperation"):
            op_name = op_el.get("name", "")
            process_ref = (op_el.findtext("processRef") or "").lstrip("/")

            op_info = OperationInfo(name=op_name, process_name="")
            if process_ref:
                self._resolve_operation_params(process_ref, op_info)

            ws.operations.append(op_info)

        return ws

    def _resolve_operation_params(self, process_ref: str, op: OperationInfo) -> None:
        """Look up the referenced IS process and extract its processParameters."""
        art = self._by_id.get(process_ref)
        if art is None:
            # Try stripping any leading path separator artifacts
            art = self._by_id.get(process_ref.lstrip("/"))
        if art is None:
            return

        op.process_name = art.name
        root = art.tree.getroot()
        proc_el = next(iter(root), None)
        if proc_el is None:
            return

        for param_el in proc_el.findall("processParameter"):
            param = self._parse_param(param_el, proc_el)
            if param.param_type == 1:
                op.inputs.append(param)
            elif param.param_type == 2:
                op.outputs.append(param)

    def _parse_param(self, el: ET.Element, proc_el: ET.Element) -> ParamInfo:
        name = el.get("name", "")
        ptype_text = el.findtext("parameterType") or "0"
        try:
            param_type = int(ptype_text)
        except ValueError:
            param_type = 0
        is_array = (el.findtext("isArrayOf") or "false").lower() == "true"
        class_id = el.findtext("classId") or ""
        type_name = self._resolve_type(class_id)
        raw_xml = self._param_to_raw_xml(el)

        return ParamInfo(
            name=name,
            param_type=param_type,
            is_array=is_array,
            class_id=class_id,
            type_name=type_name,
            raw_xml=raw_xml,
        )

    def _resolve_type(self, class_id: str) -> str:
        """Resolve a classId to a human-readable type name."""
        if not class_id:
            return "ANY"

        # Format: "{appGUID}/12.{boGUID}" or just "12.{boGUID}"
        if "/" in class_id:
            _, bo_part = class_id.rsplit("/", 1)
        else:
            bo_part = class_id

        # Check BO names by full path key
        if bo_part in self._bo_names:
            return self._bo_names[bo_part]

        # Check primitive GUIDs
        if bo_part in _PRIMITIVE_GUIDS:
            return _PRIMITIVE_GUIDS[bo_part]

        # Check known type prefixes
        for pkg_guid, type_name in _KNOWN_TYPES.items():
            if class_id.startswith(pkg_guid):
                return type_name

        # Return short GUID suffix as fallback
        return bo_part.split(".")[-1][:12] if bo_part else "ANY"

    @staticmethod
    def _param_to_raw_xml(el: ET.Element) -> str:
        """Serialize processParameter element to a clean XML string."""
        try:
            import xml.etree.ElementTree as ET
            return ET.tostring(el, encoding="unicode")
        except Exception:
            return ""
