"""
ibm_to_appian_pipeline.py — Full IBM BPM .twx → Appian Package Pipeline

Orchestrates the complete conversion from IBM TWX to Appian importable ZIP:

  1. Parse IBM TWX (BOs, env vars, service names, BPDs)
  2. Generate Appian constants from env vars
  3. Generate Appian record types from Business Objects
  4. Generate stub expression rules from services (IS/GSS/HHS)
  5. Generate process model stubs from BPDs
  6. Assemble and write the final ZIP

Usage (CLI):
    python -m appian_generator.ibm_to_appian_pipeline \\
        --twx "path/to/file.twx" \\
        --output "output/package.zip" \\
        --prefix "NCI_RB" \\
        --app-name "NCI Redención Bono"

Usage (Python):
    from appian_generator.ibm_to_appian_pipeline import AppianPipeline
    pipeline = AppianPipeline(twx_path="file.twx", app_prefix="NCI_RB")
    result = pipeline.run(output_path="output/package.zip")
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

from .uuid_registry import UUIDRegistry
from .manifest_builder import ManifestBuilder
from .constants_builder import ConstantsBuilder
from .record_type_builder import RecordTypeBuilder
from .rule_builder import RuleBuilder, RuleInput
from .process_model_builder import ProcessModelBuilder
from .group_builder import GroupBuilder
from .interface_builder import InterfaceBuilder
from .zip_packager import ZipPackager
from .ibm_twx_parser import IBMTwxParser, IBM_TYPE_MAP


class AppianPipeline:
    """
    End-to-end pipeline: IBM TWX → Appian Package ZIP.

    Phase 1: BOs → Record Types, EnvVars → Constants
    Phase 2: Service names → Expression Rule stubs
    Phase 3: BPDs → Process Model stubs (minimal scaffolding)
    """

    def __init__(self, twx_path: str, app_prefix: str = "",
                 app_name: str = "", appian_version: str = "26.3.165.0",
                 registry_path: str = None):
        self.twx_path = Path(twx_path)
        self.app_prefix = app_prefix
        self.app_name = app_name
        self.appian_version = appian_version

        # Setup registry
        reg_path = Path(registry_path) if registry_path else None
        self.registry = UUIDRegistry(reg_path)

    def run(self, output_path: str = None, verbose: bool = True) -> dict:
        """
        Execute the full pipeline.

        Returns:
            dict with run statistics and output path
        """
        stats = {
            "twx_path": str(self.twx_path),
            "app_name": "",
            "app_prefix": self.app_prefix,
            "business_objects": 0,
            "env_vars": 0,
            "processes": 0,
            "services": 0,
            "coach_views": 0,
            "record_types_generated": 0,
            "constants_generated": 0,
            "rules_generated": 0,
            "process_models_generated": 0,
            "interfaces_generated": 0,
            "groups_generated": 0,
            "output_path": "",
            "errors": [],
        }

        if verbose:
            print(f"\n{'='*60}")
            print(f"  🔷 NTT DATA — IBM BPM → Appian Pipeline")
            print(f"{'='*60}")
            print(f"  TWX: {self.twx_path.name}")

        # ── Step 1: Parse the TWX ─────────────────────────────────
        if verbose:
            print(f"\n[1/6] Parsing IBM TWX...")

        try:
            with IBMTwxParser(str(self.twx_path)) as parser:
                app_name_from_twx = parser.get_app_name()
                bos = parser.get_business_objects()
                env_vars = parser.get_env_vars()
                processes = parser.get_processes()
                services = parser.get_services()
                coach_views = parser.get_coach_views()
        except Exception as e:
            stats["errors"].append(f"TWX parse error: {e}")
            print(f"  ✗ Error parsing TWX: {e}")
            return stats

        # Determine app name and prefix
        if not self.app_name:
            self.app_name = app_name_from_twx or self.twx_path.stem
        if not self.app_prefix:
            words = self.app_name.replace("_", " ").split()[:3]
            self.app_prefix = "_".join(w[:3].upper() for w in words if w)

        stats["app_name"] = self.app_name
        stats["app_prefix"] = self.app_prefix
        stats["business_objects"] = len(bos)
        stats["env_vars"] = len(env_vars)
        stats["processes"] = len(processes)
        stats["services"] = len(services)
        stats["coach_views"] = len(coach_views)

        if verbose:
            print(f"  ✓ App: {self.app_name} (prefix: {self.app_prefix})")
            print(f"  ✓ Business Objects: {len(bos)}")
            print(f"  ✓ Environment Variables: {len(env_vars)}")
            print(f"  ✓ Business Processes (BPDs): {len(processes)}")
            print(f"  ✓ Services (IS/GSS/HHS): {len(services)}")
            print(f"  ✓ Coach Views (UI): {len(coach_views)}")

        # ── Step 2: Setup builders ────────────────────────────────
        manifest_builder = ManifestBuilder(self.registry)
        manifest = manifest_builder.create_manifest(
            app_name=self.app_name,
            app_prefix=self.app_prefix,
            appian_version=self.appian_version,
        )
        packager = ZipPackager(manifest, manifest_builder)

        constants_builder = ConstantsBuilder(
            registry=self.registry,
            app_prefix=self.app_prefix,
        )
        record_builder = RecordTypeBuilder(
            registry=self.registry,
            app_prefix=self.app_prefix,
        )
        rule_builder = RuleBuilder(
            registry=self.registry,
            app_prefix=self.app_prefix,
        )

        # Groups builder + get admin UUID first (needed by PM builder)
        group_builder = GroupBuilder(
            registry=self.registry,
            app_prefix=self.app_prefix,
            app_name=self.app_name,
        )
        admin_group_uuid = group_builder.get_admin_group_uuid()

        # PM folder UUID
        pm_folder_uuid = self.registry.get_or_create(f"PM_FOLDER:{self.app_prefix}")
        pm_builder = ProcessModelBuilder(
            registry=self.registry,
            app_prefix=self.app_prefix,
            folder_uuid=pm_folder_uuid,
            admin_group_uuid=admin_group_uuid,
        )

        # Interface builder (folder UUID determined when folder is created)
        iface_builder = InterfaceBuilder(
            registry=self.registry,
            app_prefix=self.app_prefix,
        )

        # ── Step 3: Create Security Groups ───────────────────────
        if verbose:
            print(f"\n[2/6] Generating Security Groups...")

        groups = group_builder.create_standard_groups()
        for grp in groups:
            packager.add_group(grp.uuid, group_builder.to_xml(grp))

        stats["groups_generated"] = len(groups)
        if verbose:
            print(f"  ✓ {len(groups)} groups generated: {', '.join(g.name for g in groups)}")

        # ── Step 4: Create Constants folder + env var constants ───
        if verbose:
            print(f"\n[3/6] Generating Constants ({len(env_vars)} env vars)...")

        const_folder = constants_builder.create_folder(
            folder_name=f"{self.app_prefix} Constants",
            description=f"Constants migrated from IBM BPM environment variables",
        )
        packager.add_content(const_folder.uuid, constants_builder.to_xml(const_folder))

        const_count = 0
        for ev in env_vars:
            try:
                # For test/migration packages: keep is_env_specific=False
                const = constants_builder.from_ibm_variable(
                    name=ev.name,
                    ibm_type="String",
                    value=ev.default_value,
                    description=ev.description or f"Migrated from IBM env var: {ev.name}",
                    parent_uuid=const_folder.uuid,
                    is_env_specific=False,
                )
                packager.add_content(const.uuid, constants_builder.to_xml(const))
                const_count += 1
            except Exception as e:
                stats["errors"].append(f"Constant error ({ev.name}): {e}")

        stats["constants_generated"] = const_count
        if verbose:
            print(f"  ✓ {const_count} constants generated")

        # ── Step 4: Generate Record Types from Business Objects ───
        if verbose:
            print(f"\n[4/7] Generating Record Types ({len(bos)} BOs)...")

        rt_count = 0
        for bo in bos:
            try:
                rt_uuid, rt_xml = record_builder.from_ibm_bo(bo)
                packager.add_record_type(rt_uuid, rt_xml)
                rt_count += 1
            except Exception as e:
                stats["errors"].append(f"RecordType error ({bo.name}): {e}")

        stats["record_types_generated"] = rt_count
        if verbose:
            print(f"  ✓ {rt_count} record types generated")

        # ── Step 5: Generate stub rules for services ──────────────
        if verbose:
            print(f"\n[5/7] Generating Expression Rule stubs...")

        # Rules folder
        rules_folder = constants_builder.create_folder(
            folder_name=f"{self.app_prefix} Rules",
            description=f"Expression rules migrated from IBM BPM services (stubs - require translation)",
        )
        packager.add_content(rules_folder.uuid, constants_builder.to_xml(rules_folder))

        rule_count = 0

        # Generate rules from services (IS/GSS/HHS)
        seen_rule_names = set()  # lowercase keys for case-insensitive dedup (Appian names are case-insensitive)
        for svc in services:
            try:
                rule_name = f"{self.app_prefix}_{svc.name.replace(' ', '_').replace('-', '_')}"
                if rule_name.lower() in seen_rule_names:
                    continue
                seen_rule_names.add(rule_name.lower())

                rule = rule_builder.create_stub_rule(
                    name=svc.name,
                    description=f"[{svc.service_type}] {svc.description or svc.name}",
                    inputs=[],
                    ibm_service_name=svc.name,
                    parent_uuid=rules_folder.uuid,
                )
                packager.add_content(rule.uuid, rule_builder.to_xml(rule))
                rule_count += 1
            except Exception as e:
                stats["errors"].append(f"Rule error ({svc.name}): {e}")

        # Also generate BO query rules
        for bo in bos:
            try:
                rule_name = f"get{bo.name}ById"
                full_name = f"{self.app_prefix}_{rule_name}"
                if full_name.lower() in seen_rule_names:
                    continue
                seen_rule_names.add(full_name.lower())

                rule = rule_builder.create_stub_rule(
                    name=rule_name,
                    description=f"Query rule for {bo.name} - migrated from IBM BO",
                    inputs=[RuleInput("id_int", "int", "http://www.w3.org/2001/XMLSchema",
                                      "Record ID to query")],
                    ibm_service_name=f"IBM BO: {bo.name}",
                    parent_uuid=rules_folder.uuid,
                )
                packager.add_content(rule.uuid, rule_builder.to_xml(rule))
                rule_count += 1
            except Exception as e:
                stats["errors"].append(f"BO rule error ({bo.name}): {e}")

        stats["rules_generated"] = rule_count
        if verbose:
            print(f"  ✓ {rule_count} rule stubs generated ({len(services)} services + {len(bos)} BO queries)")

        # ── Step 6: Generate Process Model stubs from BPDs ────────
        if verbose:
            print(f"\n[6/7] Generating Process Model stubs ({len(processes)} BPDs)...")

        # Add PM folder
        pm_folder_xml = pm_builder.build_pm_folder(pm_folder_uuid)
        packager.add_process_model_folder(pm_folder_uuid, pm_folder_xml)

        pm_count = 0
        for proc in processes:
            try:
                pm = pm_builder.from_ibm_process(proc, bos)
                pm_xml = pm_builder.to_xml(pm)
                packager.add_process_model(pm.uuid, pm_xml)
                pm_count += 1
            except Exception as e:
                stats["errors"].append(f"ProcessModel error ({proc.name}): {e}")

        stats["process_models_generated"] = pm_count
        if verbose:
            print(f"  ✓ {pm_count} process model stubs generated")

        # ── Step 7: Generate Interface stubs from Coach Views ─────
        if verbose:
            print(f"\n[7/8] Generating Interface stubs ({len(coach_views)} Coach Views)...")

        # Create Interfaces folder
        iface_folder = constants_builder.create_folder(
            folder_name=f"{self.app_prefix} Interfaces",
            description="Interfaces migrated from IBM BPM Coach Views (stubs - require implementation)",
        )
        packager.add_content(iface_folder.uuid, constants_builder.to_xml(iface_folder))
        # Update interface builder with correct folder UUID
        iface_builder.default_parent_uuid = iface_folder.uuid

        iface_count = 0
        seen_iface_names = set()  # lowercase for case-insensitive dedup
        for cv in coach_views:
            try:
                iface_name = f"{self.app_prefix}_{cv.name.replace(' ', '_').replace('-', '_')}"
                if iface_name.lower() in seen_iface_names:
                    continue
                seen_iface_names.add(iface_name.lower())

                iface = iface_builder.from_ibm_coach_view(
                    name=cv.name,
                    ibm_id=cv.id,
                    description=cv.description,
                    parent_uuid=iface_folder.uuid,
                )
                packager.add_content(iface.uuid, iface_builder.to_xml(iface))
                iface_count += 1
            except Exception as e:
                stats["errors"].append(f"Interface error ({cv.name}): {e}")

        stats["interfaces_generated"] = iface_count
        if verbose:
            print(f"  ✓ {iface_count} interface stubs generated")

        # ── Step 8: Build ZIP ─────────────────────────────────────
        if verbose:
            print(f"\n[8/8] Building Appian package ZIP...")

        if not output_path:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            safe_name = self.app_name.replace(" ", "_").replace("/", "-")
            output_path = str(output_dir / f"{safe_name}_appian_package.zip")

        try:
            zip_path = packager.build(output_path)
            stats["output_path"] = str(zip_path)
            if verbose:
                summary = packager.summary()
                print(f"  ✓ ZIP created: {zip_path}")
                print(f"  ✓ Total objects: {summary['total_objects']}")
        except Exception as e:
            stats["errors"].append(f"ZIP build error: {e}")
            if verbose:
                print(f"  ✗ ZIP error: {e}")

        # Final summary
        if verbose:
            print(f"\n{'='*60}")
            print(f"  ✅ Pipeline Complete")
            print(f"{'='*60}")
            print(f"  Constants:      {stats['constants_generated']}")
            print(f"  Record Types:   {stats['record_types_generated']}")
            print(f"  Rule Stubs:     {stats['rules_generated']}")
            print(f"  Interfaces:     {stats['interfaces_generated']}")
            print(f"  Process Models: {stats['process_models_generated']}")
            print(f"  Groups:         {stats['groups_generated']}")
            if stats["errors"]:
                print(f"  ⚠ Errors:       {len(stats['errors'])}")
                for err in stats["errors"][:5]:
                    print(f"    - {err}")
            print(f"\n  📦 Output: {stats['output_path']}")
            print(f"{'='*60}\n")

        return stats


def main():
    parser = argparse.ArgumentParser(
        description="NTT DATA — IBM BPM .twx → Appian Package Generator"
    )
    parser.add_argument("twx", help="Path to the .twx file")
    parser.add_argument("--output", "-o", help="Output ZIP path", default=None)
    parser.add_argument("--prefix", "-p", help="Appian app prefix (e.g. NCI_RB)", default="")
    parser.add_argument("--app-name", "-n", help="Appian application name", default="")
    parser.add_argument("--appian-version", default="26.3.165.0",
                        help="Target Appian version (default: 26.3.165.0)")
    parser.add_argument("--registry", help="Path to UUID registry JSON file", default=None)
    parser.add_argument("--json", action="store_true", help="Output stats as JSON")

    args = parser.parse_args()

    pipeline = AppianPipeline(
        twx_path=args.twx,
        app_prefix=args.prefix,
        app_name=args.app_name,
        appian_version=args.appian_version,
        registry_path=args.registry,
    )

    stats = pipeline.run(output_path=args.output, verbose=not args.json)

    if args.json:
        print(json.dumps(stats, indent=2, ensure_ascii=False))

    if stats["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
