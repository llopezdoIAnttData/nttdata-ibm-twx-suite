"""
appian_generator — NTT DATA IBM BPM → Appian Package Generator
==============================================================
Generates Appian-importable ZIP packages from IBM BPM .twx extracted data.

Real Appian ZIP structure (v26.3+):
    <package>.zip/
    ├── META-INF/
    │   └── MANIFEST.MF          ← Appian version + export date only
    ├── application/
    │   └── <uuid>.xml           ← applicationHaul (lists all UUIDs)
    ├── content/
    │   └── <uuid>.xml           ← contentHaul: constant/rule/interface/
    │                               outboundIntegration/rulesFolder/decision
    ├── processModel/
    │   └── <uuid>.xml           ← processModelHaul (BPMN-like)
    ├── processModelFolder/
    │   └── <uuid>.xml
    ├── recordType/
    │   └── <uuid>.xml           ← recordTypeHaul (DB table mapping)
    └── group/
        └── <uuid>.xml

Modules:
    constants_builder     — IBM vars/constants → Appian <constant>
    record_type_builder   — IBM BOs → Appian <recordType> (DB-backed)
    rule_builder          — IBM IS (simple) → Appian <rule>
    process_model_builder — IBM BPD → Appian <processModelHaul>
    manifest_builder      — Generates MANIFEST.MF + applicationHaul
    zip_packager          — Assembles final .zip from all components
    deploy_client         — REST API import via /deployment-management/v2
    uuid_registry         — Consistent UUID generation and tracking
"""

__version__ = "0.1.0"
__author__ = "NTT DATA · llopezdo@emeal.nttdata.com"

from .uuid_registry import UUIDRegistry
from .manifest_builder import ManifestBuilder
from .constants_builder import ConstantsBuilder
from .zip_packager import ZipPackager
from .ibm_twx_parser import IBMTwxParser, IBMBusinessObject, IBMField, IBMEnvVar
from .record_type_builder import RecordTypeBuilder
from .rule_builder import RuleBuilder, RuleInput
from .ibm_to_appian_pipeline import AppianPipeline
from .deploy_client import AppianDeployClient

__all__ = [
    "UUIDRegistry", "ManifestBuilder", "ConstantsBuilder", "ZipPackager",
    "IBMTwxParser", "IBMBusinessObject", "IBMField", "IBMEnvVar",
    "RecordTypeBuilder", "RuleBuilder", "RuleInput",
    "AppianPipeline", "AppianDeployClient",
]
