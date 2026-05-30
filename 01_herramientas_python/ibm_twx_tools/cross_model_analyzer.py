"""Cross-TWX Data Model Pattern Analyzer.

Loads N .twx files, extracts the Business Object model from each one and
produces a cross-application pattern report:

  - **Shared / Reusable**  : BOs whose name appears in 2+ TWX files.
      Flags whether the definition is *identical* or *divergent* across files.
  - **Structural clusters**: BOs with *different names* but the same field
      signature — strong candidates for consolidation into a shared toolkit.
  - **Unique**             : BOs that exist only in a single TWX file.

Usage (programmatic):
    from ibm_twx_tools.cross_model_analyzer import CrossModelAnalyzer
    report = CrossModelAnalyzer(["a.twx", "b.twx", "c.twx"]).analyze()
    print(report.to_markdown())
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .twx_parser import TWXParser
from .entity_extractor import EntityExtractor, BusinessObject, BOField
from .parametria_extractor import classify_bo, CATALOG_KEYWORDS, DOMAIN_ENTITY_FIELDS


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BOAppearance:
    """One occurrence of a BO inside a specific TWX file."""
    twx_name: str
    twx_path: str
    bo: BusinessObject


@dataclass
class SharedBO:
    """A Business Object whose name is present in 2+ TWX files."""
    name: str
    appearances: list[BOAppearance]
    is_identical: bool       # True when field definitions are 100 % equal
    divergent_fields: list[str]  # Field names that differ across files
    f3_category: str = "dto"     # domain_entity | dto | catalog
    f3_appian_target: str = "CDT / variable de proceso local"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "found_in": [a.twx_name for a in self.appearances],
            "reusable_as_is": self.is_identical,
            "divergent_fields": self.divergent_fields,
            "f3_category": self.f3_category,
            "f3_appian_target": self.f3_appian_target,
            "per_file_definition": [
                {
                    "twx": a.twx_name,
                    "fields": [
                        {
                            "name": f.name,
                            "type": f.type_ref,
                            "is_list": f.is_list,
                            "required": f.required,
                        }
                        for f in a.bo.fields
                    ],
                }
                for a in self.appearances
            ],
        }


@dataclass
class StructuralCluster:
    """BOs with different names but the same field signature."""
    cluster_id: int
    field_signature: str      # Human-readable description of the common structure
    raw_signature: frozenset  # frozenset of (name, type) tuples
    members: list[dict]       # [{"twx": ..., "bo_name": ..., "description": ...}]

    def to_dict(self) -> dict:
        return {
            "cluster_id": self.cluster_id,
            "field_signature": self.field_signature,
            "member_count": len(self.members),
            "members": self.members,
        }


@dataclass
class CrossModelReport:
    """Complete result of a cross-TWX model analysis."""
    twx_files: list[str]
    per_twx: dict[str, list[dict]]          # twx_name → list of BO dicts
    shared: list[SharedBO]                  # BOs in ≥ 2 TWX files
    unique: dict[str, list[str]]            # twx_name → BO names only in that TWX
    structural_clusters: list[StructuralCluster]  # same structure, different names
    stats: dict

    # ------------------------------------------------------------------ output

    def to_dict(self) -> dict:
        return {
            "stats": self.stats,
            "twx_files": self.twx_files,
            "shared_reusable": [s.to_dict() for s in self.shared],
            "unique_per_twx": self.unique,
            "structural_clusters": [c.to_dict() for c in self.structural_clusters],
            "per_twx_model": self.per_twx,
        }

    def to_markdown(self) -> str:
        lines: list[str] = []
        _h = lines.append

        _h("# Cross-TWX Data Model Pattern Report")
        _h("")
        _h(f"**Analyzed files:** {len(self.twx_files)}")
        for f in self.twx_files:
            _h(f"- `{f}`")
        _h("")

        # ── Stats ──────────────────────────────────────────────────────────
        _h("## Summary")
        _h("")
        _h("| Metric | Value |")
        _h("|--------|-------|")
        for k, v in self.stats.items():
            _h(f"| {k.replace('_', ' ').title()} | {v} |")
        _h("")

        # ── Shared / Reusable ──────────────────────────────────────────────
        _h("## Shared / Reusable Business Objects")
        _h("")
        if not self.shared:
            _h("_No Business Objects with the same name were found across multiple TWX files._")
        else:
            for s in self.shared:
                icon = "✅" if s.is_identical else "⚠️"
                _h(f"### {icon} `{s.name}`")
                _h("")
                _h(f"- **Found in:** {', '.join(f'`{a.twx_name}`' for a in s.appearances)}")
                _h(f"- **Identical definition:** {'Yes — safe to reuse as-is' if s.is_identical else 'No — definitions diverge'}")
                if s.divergent_fields:
                    _h(f"- **Divergent fields:** {', '.join(f'`{f}`' for f in s.divergent_fields)}")
                _h("")
                _h("| File | Fields |")
                _h("|------|--------|")
                for a in s.appearances:
                    field_summary = ", ".join(
                        f"`{f.name}:{f.type_ref}`{'[]' if f.is_list else ''}"
                        for f in a.bo.fields
                    ) or "_no fields_"
                    _h(f"| `{a.twx_name}` | {field_summary} |")
                _h("")

        # ── Structural clusters ────────────────────────────────────────────
        _h("## Structural Clusters (Same Structure, Different Names)")
        _h("")
        _h("> These Business Objects share the same field signature and are strong candidates")
        _h("> for consolidation into a shared toolkit or common data model.")
        _h("")
        if not self.structural_clusters:
            _h("_No structural clusters detected._")
        else:
            for c in self.structural_clusters:
                _h(f"### Cluster {c.cluster_id}")
                _h("")
                _h(f"**Field signature:** `{c.field_signature}`")
                _h("")
                _h("| TWX File | BO Name | Description |")
                _h("|----------|---------|-------------|")
                for m in c.members:
                    _h(f"| `{m['twx']}` | `{m['bo_name']}` | {m.get('description') or '—'} |")
                _h("")

        # ── Unique per TWX ─────────────────────────────────────────────────
        _h("## Unique Business Objects (per TWX)")
        _h("")
        for twx_name, bo_names in self.unique.items():
            _h(f"### `{twx_name}`")
            _h("")
            if bo_names:
                for name in sorted(bo_names):
                    _h(f"- `{name}`")
            else:
                _h("_All BOs are shared with at least one other TWX file._")
            _h("")

        # ── Per-TWX full model ─────────────────────────────────────────────
        _h("## Full Data Model per TWX")
        _h("")
        for twx_name, bos in self.per_twx.items():
            _h(f"### `{twx_name}`")
            _h("")
            if not bos:
                _h("_No Business Objects found._")
            else:
                for bo in bos:
                    _h(f"#### `{bo['name']}`")
                    if bo.get("description"):
                        _h(f"> {bo['description']}")
                    if bo.get("parent"):
                        _h(f"> Extends: `{bo['parent']}`")
                    _h("")
                    if bo["fields"]:
                        _h("| Field | Type | List | Required | Default |")
                        _h("|-------|------|------|----------|---------|")
                        for f in bo["fields"]:
                            _h(
                                f"| `{f['name']}` | `{f['type']}` "
                                f"| {'✓' if f['is_list'] else ''} "
                                f"| {'✓' if f['required'] else ''} "
                                f"| {f.get('default') or ''} |"
                            )
                    else:
                        _h("_No fields declared._")
                    _h("")
            _h("")

        return "\n".join(lines)

    def to_html(self) -> str:
        """Generates a full professional HTML report for this analysis."""
        from .cross_model_html import generate_cross_model_html
        return generate_cross_model_html(self)


# ─────────────────────────────────────────────────────────────────────────────
# Analyzer
# ─────────────────────────────────────────────────────────────────────────────

class CrossModelAnalyzer:
    """Analyzes the data model across multiple TWX files.

    Args:
        twx_paths: List of paths to .twx files.
    """

    def __init__(self, twx_paths: list[str]):
        if not twx_paths:
            raise ValueError("At least one TWX file must be provided.")
        self.twx_paths = [Path(p) for p in twx_paths]

    # ------------------------------------------------------------------ public

    def analyze(self) -> CrossModelReport:
        """Run the full cross-model analysis and return a CrossModelReport."""

        # Step 1: extract BOs from each TWX — keep (name, path, bos) together
        twx_entries: list[tuple[str, str, list[BusinessObject]]] = []
        for p in self.twx_paths:
            package = TWXParser(str(p)).parse()
            extractor = EntityExtractor(package)
            bos = extractor.extract()
            twx_name = package.app_name or p.stem
            twx_entries.append((twx_name, str(p), bos))

        per_twx_bos: dict[str, list[BusinessObject]] = {
            name: bos for name, _, bos in twx_entries
        }

        # Step 2: build name → [BOAppearance] index
        name_index: dict[str, list[BOAppearance]] = defaultdict(list)
        for twx_name, twx_path, bos in twx_entries:
            for bo in bos:
                name_index[bo.name].append(
                    BOAppearance(twx_name=twx_name, twx_path=twx_path, bo=bo)
                )

        # Step 3: classify shared vs unique
        shared_list: list[SharedBO] = []
        unique_names: dict[str, list[str]] = {n: [] for n in per_twx_bos}

        for bo_name, appearances in name_index.items():
            if len(appearances) >= 2:
                shared_bo = self._build_shared(bo_name, appearances)
                # Classify using first appearance BO
                category = classify_bo(appearances[0].bo, set())
                shared_bo.f3_category = category
                if category == "domain_entity":
                    shared_bo.f3_appian_target = "Record Type (tabla NOV_*)"
                elif category == "catalog":
                    shared_bo.f3_appian_target = "skip (tabla catálogo existente)"
                else:
                    shared_bo.f3_appian_target = "CDT / variable de proceso local"
                shared_list.append(shared_bo)
            else:
                # Only one appearance
                twx_name = appearances[0].twx_name
                if twx_name in unique_names:
                    unique_names[twx_name].append(bo_name)

        # Sort shared by reusability (identical first) then name
        shared_list.sort(key=lambda s: (not s.is_identical, s.name))

        # Step 4: structural clusters (same field signature, different names)
        clusters = self._find_structural_clusters(name_index, per_twx_bos)

        # Step 5: build per_twx output dicts
        per_twx_dicts = {
            twx_name: [bo.to_dict() for bo in bos]
            for twx_name, bos in per_twx_bos.items()
        }

        # Step 6: stats
        total_distinct = len(name_index)
        shared_count = len(shared_list)
        identical_count = sum(1 for s in shared_list if s.is_identical)
        divergent_count = shared_count - identical_count
        total_unique = sum(len(v) for v in unique_names.values())

        stats = {
            "twx_files_analyzed": len(per_twx_bos),
            "total_distinct_bo_names": total_distinct,
            "shared_across_files": shared_count,
            "shared_identical_definition": identical_count,
            "shared_divergent_definition": divergent_count,
            "unique_to_single_file": total_unique,
            "structural_clusters_found": len(clusters),
        }

        return CrossModelReport(
            twx_files=[str(p) for p in self.twx_paths],
            per_twx=per_twx_dicts,
            shared=shared_list,
            unique=unique_names,
            structural_clusters=clusters,
            stats=stats,
        )

    # ------------------------------------------------------------------ private

    def _build_shared(self, name: str, appearances: list[BOAppearance]) -> SharedBO:
        """Compares field definitions across appearances and flags divergences."""
        # Build field-set per appearance
        field_sets: list[dict[str, tuple]] = []
        for a in appearances:
            field_sets.append({
                f.name: (f.type_ref, f.is_list, f.required)
                for f in a.bo.fields
            })

        reference = field_sets[0]
        divergent: set[str] = set()

        for fs in field_sets[1:]:
            all_keys = set(reference) | set(fs)
            for k in all_keys:
                if reference.get(k) != fs.get(k):
                    divergent.add(k)

        return SharedBO(
            name=name,
            appearances=appearances,
            is_identical=len(divergent) == 0,
            divergent_fields=sorted(divergent),
        )

    def _build_signature(self, bo: BusinessObject) -> frozenset:
        """Normalized field signature: frozenset of (field_name, normalized_type)."""
        return frozenset(
            (f.name.lower(), f.type_ref.lower().split(".")[-1])
            for f in bo.fields
            if f.name
        )

    def _sig_to_str(self, sig: frozenset) -> str:
        """Human-readable signature string."""
        parts = sorted(f"{name}:{typ}" for name, typ in sig)
        return ", ".join(parts) if parts else "(empty)"

    def _find_structural_clusters(
        self,
        name_index: dict[str, list[BOAppearance]],
        per_twx_bos: dict[str, list[BusinessObject]],
    ) -> list[StructuralCluster]:
        """Groups BOs with identical field signature but different names."""

        # sig → list of (twx_name, bo_name, description)
        sig_index: dict[frozenset, list[dict]] = defaultdict(list)

        for bo_name, appearances in name_index.items():
            for a in appearances:
                if not a.bo.fields:
                    continue
                sig = self._build_signature(a.bo)
                sig_index[sig].append({
                    "twx": a.twx_name,
                    "bo_name": bo_name,
                    "description": a.bo.description,
                })

        # Only keep clusters where there are 2+ *different* BO names
        clusters: list[StructuralCluster] = []
        cluster_id = 1
        for sig, members in sig_index.items():
            distinct_names = {m["bo_name"] for m in members}
            if len(distinct_names) < 2:
                continue  # skip — all same name (already in shared)
            clusters.append(StructuralCluster(
                cluster_id=cluster_id,
                field_signature=self._sig_to_str(sig),
                raw_signature=sig,
                members=members,
            ))
            cluster_id += 1

        # Sort by cluster size descending
        clusters.sort(key=lambda c: len(c.members), reverse=True)
        return clusters
