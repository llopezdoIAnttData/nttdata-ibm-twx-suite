"""
ibm_twx_parser.py — Direct XML parser for IBM BPM .twx files

Reads the raw XML inside the TWX ZIP to extract:
  - Business Objects (12.xxx.xml) with full field definitions
  - Environment Variables (62.xxx.xml) → Appian Constants
  - Services metadata (1.xxx.xml)
  - Process metadata (25.xxx.xml)

This is a low-level parser that provides data for the appian_generator builders.
Does NOT depend on the ibm_twx_tools CLI — reads ZIP directly.
"""

import zipfile
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
import xml.etree.ElementTree as ET


# IBM XSD type namespace
IBM_XSD_NS = "http://www.w3.org/2001/XMLSchema"
IBM_APPIAN_NS = "http://www.appian.com/ae/types/2009"

# Map IBM typeName → (appian_type_name, appian_namespace)
IBM_TYPE_MAP = {
    "string":   ("string",  IBM_XSD_NS),
    "String":   ("string",  IBM_XSD_NS),
    "int":      ("int",     IBM_XSD_NS),
    "integer":  ("int",     IBM_XSD_NS),
    "Integer":  ("int",     IBM_XSD_NS),
    "long":     ("long",    IBM_XSD_NS),
    "decimal":  ("decimal", IBM_XSD_NS),
    "Decimal":  ("decimal", IBM_XSD_NS),
    "float":    ("decimal", IBM_XSD_NS),
    "double":   ("decimal", IBM_XSD_NS),
    "boolean":  ("boolean", IBM_XSD_NS),
    "Boolean":  ("boolean", IBM_XSD_NS),
    "date":     ("date",    IBM_XSD_NS),
    "dateTime": ("dateTime", IBM_XSD_NS),
    "Date":     ("date",    IBM_XSD_NS),
    "DateTime": ("dateTime", IBM_XSD_NS),
    "ANY":      ("Variant", IBM_APPIAN_NS),
    "Object":   ("Variant", IBM_APPIAN_NS),
}


@dataclass
class IBMField:
    """A field in an IBM Business Object."""
    name: str
    type_name: str          # XSD type (string, int, decimal, etc.) or BO name
    type_ns: str            # XSD namespace
    is_array: bool = False
    class_ref: str = ""     # classRef attribute (to resolve custom types)
    description: str = ""
    is_custom_type: bool = False  # True if references another BO


@dataclass
class IBMBusinessObject:
    """An IBM BPM Business Object (twClass)."""
    id: str                 # e.g. "12.062776b3-..."
    name: str
    guid: str = ""
    description: str = ""
    fields: list = field(default_factory=list)  # list of IBMField


@dataclass
class IBMEnvVar:
    """An IBM BPM environment variable."""
    id: str
    name: str
    default_value: str = ""
    description: str = ""
    type_name: str = "string"


@dataclass
class IBMService:
    """An IBM BPM service (IS/HHS/GSS)."""
    id: str
    name: str
    service_type: str = ""  # "IS", "HHS", "GSS"
    description: str = ""


@dataclass
class IBMCoachView:
    """An IBM BPM Coach View (UI component)."""
    id: str
    name: str
    description: str = ""


@dataclass
class IBMProcessParam:
    """A parameter of an IBM BPD process."""
    name: str
    param_type: int          # 1=input, 2=output
    is_array: bool = False
    class_id: str = ""       # e.g. "ns/12.xxx" for BO references
    bo_name: str = ""        # resolved BO name (filled in later)
    xsd_type: str = "string" # fallback XSD type if not BO


@dataclass
class IBMProcess:
    """An IBM BPM Business Process Diagram (BPD)."""
    id: str
    name: str
    description: str = ""
    guid: str = ""
    params: list = field(default_factory=list)  # list of IBMProcessParam


class IBMTwxParser:
    """
    Parses an IBM BPM .twx file directly from its ZIP structure.

    Usage:
        parser = IBMTwxParser("path/to/file.twx")
        bos = parser.get_business_objects()
        env_vars = parser.get_env_vars()
    """

    def __init__(self, twx_path: str):
        self.twx_path = Path(twx_path)
        self._zip: Optional[zipfile.ZipFile] = None
        self._object_index: dict[str, str] = {}  # filename → object type prefix
        self._opened = False

    def __enter__(self):
        self._zip = zipfile.ZipFile(self.twx_path, "r")
        self._opened = True
        self._build_index()
        return self

    def __exit__(self, *args):
        if self._zip:
            self._zip.close()

    def _build_index(self):
        """Index all objects/ files by type prefix."""
        for name in self._zip.namelist():
            if name.startswith("objects/") and name.endswith(".xml"):
                fname = name.split("/")[-1]
                prefix = fname.split(".")[0]
                self._object_index[fname] = prefix

    def _read_xml(self, path: str) -> Optional[ET.Element]:
        """Read and parse an XML file from the ZIP."""
        try:
            with self._zip.open(path) as f:
                content = f.read().decode("utf-8", errors="replace")
                return ET.fromstring(content)
        except Exception:
            return None

    def _get_text(self, elem: ET.Element, tag: str, default: str = "") -> str:
        """Get text from a child element."""
        child = elem.find(tag)
        if child is None:
            return default
        if child.get("isNull") == "true":
            return default
        return (child.text or "").strip()

    def get_business_objects(self) -> list[IBMBusinessObject]:
        """Extract all Business Objects with their fields."""
        bos = []
        bo_files = [f for f, p in self._object_index.items() if p == "12"]

        for fname in bo_files:
            root = self._read_xml(f"objects/{fname}")
            if root is None:
                continue

            tw_class = root.find("twClass")
            if tw_class is None:
                continue

            bo_id = tw_class.get("id", "")
            bo_name = tw_class.get("name", "")
            description = self._get_text(tw_class, "description")
            guid = self._get_text(tw_class, "guid")

            fields = []
            definition = tw_class.find("definition")
            if definition is not None:
                for prop in definition.findall("property"):
                    prop_name = self._get_text(prop, "name")
                    if not prop_name:
                        continue

                    is_array_text = self._get_text(prop, "arrayProperty", "false")
                    is_array = is_array_text.lower() == "true"
                    class_ref = self._get_text(prop, "classRef")
                    prop_desc = self._get_text(prop, "description")

                    # Try to get type from annotation
                    type_name = "string"
                    type_ns = IBM_XSD_NS
                    is_custom = False

                    annotation = prop.find("annotation")
                    if annotation is not None:
                        ann_type = self._get_text(annotation, "typeName")
                        ann_ns = self._get_text(annotation, "typeNamespace")
                        if ann_type and ann_type not in ("", "null"):
                            type_name = ann_type
                            type_ns = ann_ns or IBM_XSD_NS
                        elif ann_type == "" and class_ref:
                            # Custom type reference — will be resolved later
                            is_custom = True
                            type_name = class_ref  # placeholder

                    fields.append(IBMField(
                        name=prop_name,
                        type_name=type_name,
                        type_ns=type_ns,
                        is_array=is_array,
                        class_ref=class_ref,
                        description=prop_desc,
                        is_custom_type=is_custom,
                    ))

            bos.append(IBMBusinessObject(
                id=bo_id,
                name=bo_name,
                guid=guid,
                description=description,
                fields=fields,
            ))

        return bos

    def get_env_vars(self) -> list[IBMEnvVar]:
        """Extract environment variables (→ Appian constants)."""
        env_vars = []
        env_files = [f for f, p in self._object_index.items() if p == "62"]

        for fname in env_files:
            root = self._read_xml(f"objects/{fname}")
            if root is None:
                continue

            ev_set = root.find("environmentVariableSet")
            if ev_set is None:
                continue

            for env_var in ev_set.findall("envVar"):
                var_name = env_var.get("name", "")
                var_id = self._get_text(env_var, "envVarId")
                var_desc = self._get_text(env_var, "description")
                default_val = self._get_text(env_var, "defaultValue")

                # Get first envVarDefault value
                first_default = env_var.find("envVarDefault")
                if first_default is not None:
                    val = self._get_text(first_default, "value")
                    if val:
                        default_val = val

                env_vars.append(IBMEnvVar(
                    id=var_id,
                    name=var_name,
                    default_value=default_val,
                    description=var_desc,
                ))

        return env_vars

    def get_app_name(self) -> str:
        """Get the application name from META-INF/metadata.xml."""
        try:
            root = self._read_xml("META-INF/metadata.xml")
            if root is not None:
                name = root.find(".//name")
                if name is not None:
                    return (name.text or "").strip()
        except Exception:
            pass
        return ""

    def resolve_bo_by_id(self, bo_id: str, bos: list[IBMBusinessObject]) -> Optional[IBMBusinessObject]:
        """Find a BO by its id."""
        for bo in bos:
            if bo.id == bo_id:
                return bo
        return None

    def get_processes(self) -> list:
        """Extract all BPDs (Business Process Diagrams) with their parameters."""
        processes = []
        bpd_files = [f for f, p in self._object_index.items() if p == "25"]

        for fname in bpd_files:
            root = self._read_xml(f"objects/{fname}")
            if root is None:
                continue

            bpd = root.find("bpd")
            if bpd is None:
                # Some BPD files use different root structures
                bpd = root

            bpd_id = bpd.get("id", fname.replace(".xml", ""))
            bpd_name = bpd.get("name", "")
            if not bpd_name:
                continue

            desc_el = bpd.find("description")
            description = (desc_el.text or "").strip() if desc_el is not None and desc_el.get("isNull") != "true" else ""
            guid_el = bpd.find("guid")
            guid = (guid_el.text or "").strip() if guid_el is not None else ""

            params = []
            for param in bpd.findall("bpdParameter"):
                param_name = param.get("name", "")
                if not param_name:
                    continue

                # parameterType: 1=input, 2=output
                ptype_el = param.find("parameterType")
                param_type = int(ptype_el.text or "1") if ptype_el is not None else 1

                is_arr_el = param.find("isArrayOf")
                is_array = (is_arr_el.text or "false").lower() == "true" if is_arr_el is not None else False

                class_id_el = param.find("classId")
                class_id = (class_id_el.text or "").strip() if class_id_el is not None and class_id_el.get("isNull") != "true" else ""

                params.append(IBMProcessParam(
                    name=param_name,
                    param_type=param_type,
                    is_array=is_array,
                    class_id=class_id,
                ))

            processes.append(IBMProcess(
                id=bpd_id,
                name=bpd_name,
                description=description,
                guid=guid,
                params=params,
            ))

        return processes

    def get_services(self) -> list:
        """Extract all services (GSS, HHS, IS) with name and type."""
        services = []
        # Service files use prefix "1"
        svc_files = [f for f, p in self._object_index.items() if p == "1"]

        SERVICE_TYPE_MAP = {
            "GSS": "General System Service (GSS)",
            "HHS": "Human Service (HHS)",
            "IS":  "Integration Service (IS)",
        }

        for fname in svc_files:
            root = self._read_xml(f"objects/{fname}")
            if root is None:
                continue

            # Detect service type from root element or child elements
            svc_type = "GSS"
            if root.find(".//isAdHoc") is not None:
                svc_type = "HHS"
            if root.find(".//integrationStepDefinition") is not None or \
               root.find(".//serverScriptProperties") is not None:
                svc_type = "IS"

            # Try various name locations
            name = ""
            for path in ["./service", "./humanService", "./integrationService"]:
                el = root.find(path)
                if el is not None:
                    name = el.get("name", "")
                    break
            if not name:
                # Try root element name attribute
                name = root.get("name", "")
            if not name:
                # Try first child with name attribute
                for child in root:
                    n = child.get("name", "")
                    if n:
                        name = n
                        break
            if not name:
                continue

            desc_el = root.find(".//description")
            description = ""
            if desc_el is not None and desc_el.get("isNull") != "true":
                description = (desc_el.text or "").strip()

            svc_id = fname.replace(".xml", "")
            services.append(IBMService(
                id=svc_id,
                name=name,
                service_type=SERVICE_TYPE_MAP.get(svc_type, svc_type),
                description=description,
            ))

        return services

    def get_coach_views(self) -> list:
        """Extract all Coach Views (UI components → Appian Interface stubs)."""
        coach_views = []
        cv_files = [f for f, p in self._object_index.items() if p == "64"]

        for fname in cv_files:
            root = self._read_xml(f"objects/{fname}")
            if root is None:
                continue

            cv = root.find("coachView")
            if cv is None:
                cv = root

            cv_id = cv.get("id", fname.replace(".xml", ""))
            cv_name = cv.get("name", "")
            if not cv_name:
                continue

            desc_el = cv.find("description")
            description = ""
            if desc_el is not None and desc_el.get("isNull") != "true":
                description = (desc_el.text or "").strip()

            coach_views.append(IBMCoachView(
                id=cv_id,
                name=cv_name,
                description=description,
            ))

        return coach_views
