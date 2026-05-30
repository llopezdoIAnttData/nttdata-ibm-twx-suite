"""
NTTDATA IBM TWX Reverse Engineering Suite — CLI
================================================
Usage:
    python -m ibm_twx_tools <command> <file.twx> [options]
    python -m ibm_twx_tools cross-model <file1.twx> <file2.twx> ... [options]

Commands (single file):
    analyze    Full analysis summary
    entities   Extract Business Objects
    services   Extract services and scripts
    flows      Map process flows (Mermaid)
    deps       Dependency call graph
    docs       Generate full Markdown documentation
    scripts    Dump all embedded scripts
    endpoints  List all external endpoints
    entries    Show entry points

Commands (multi-file):
    cross-model  Cross-TWX data model pattern analysis
                 Identifies shared/reusable BOs, structural clusters and
                 unique entities across N TWX files.
"""

import argparse
import json
import re
import sys
import os
from pathlib import Path

# Ensure stdout handles non-ASCII characters on Windows (e.g., Spanish characters)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from . import __version__, __corporate__, __product__
from .twx_parser import TWXParser
from .entity_extractor import EntityExtractor
from .service_extractor import ServiceExtractor
from .flow_mapper import FlowMapper
from .doc_generator import DocGenerator
from .cross_model_analyzer import CrossModelAnalyzer
from .parametria_extractor import ParametriaExtractor
from .web_service_extractor import BPDVariableExtractor, WebServiceExtractor
from .is_params_html import generate_html as _is_params_generate_html
from .banner import print_banner


def cmd_analyze(args, package):
    print(json.dumps(package.summary, indent=2, ensure_ascii=False))


def cmd_entities(args, package):
    extractor = EntityExtractor(package)
    entities = extractor.extract()
    output = [bo.to_dict() for bo in entities]
    print(json.dumps(output, indent=2, ensure_ascii=False))


def cmd_services(args, package):
    extractor = ServiceExtractor(package)
    services = extractor.extract()
    output = [svc.to_dict() for svc in services]
    print(json.dumps(output, indent=2, ensure_ascii=False))


def cmd_flows(args, package):
    mapper = FlowMapper(package)
    flows = mapper.extract_flows()
    for flow in flows:
        print(f"\n{'='*60}")
        print(f"# {flow.name} ({flow.artifact_type})")
        print(f"{'='*60}")
        print(flow.to_mermaid())


def cmd_deps(args, package):
    mapper = FlowMapper(package)
    graph = mapper.build_dependency_graph()
    print(graph.to_mermaid())


def cmd_docs(args, package):
    generator = DocGenerator(package, version=__version__)
    doc = generator.generate_full()

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(doc, encoding="utf-8")
        print(f"Documentation written to: {output_path}")
    else:
        print(doc)


def cmd_scripts(args, package):
    extractor = ServiceExtractor(package)
    scripts = extractor.extract_scripts()
    for script in scripts:
        print(f"\n{'─'*60}")
        print(f"# Artifact: {script['artifact']}")
        print(f"# Step:     {script.get('step_name') or script.get('step_id', '')}")
        print(f"# Language: {script['language']}")
        print(f"{'─'*60}")
        print(script["code"])


def cmd_endpoints(args, package):
    extractor = ServiceExtractor(package)
    endpoints = extractor.extract_rest_endpoints()
    print(json.dumps(endpoints, indent=2, ensure_ascii=False))


def cmd_entries(args, package):
    mapper = FlowMapper(package)
    entries = mapper.find_entry_points()
    print(json.dumps(entries, indent=2, ensure_ascii=False))


def cmd_parametria(args, package):
    """Ciclo 10: F3 Architecture Mapping — classifica BOs, descompone BPDs en procesos
    efímeros y genera template de parametría para arquitectura F3."""
    extractor = ParametriaExtractor(package)
    report = extractor.extract()

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ext = output_path.suffix.lower()
        if ext == ".json":
            output_path.write_text(report.to_json(), encoding="utf-8")
        else:
            output_path.write_text(report.to_json(), encoding="utf-8")
        print(f"[OK] Reporte F3 guardado en: {output_path}")
        print(report.to_summary())
    else:
        print(report.to_json())


COMMANDS = {
    "analyze":    cmd_analyze,
    "entities":   cmd_entities,
    "services":   cmd_services,
    "flows":      cmd_flows,
    "deps":       cmd_deps,
    "docs":       cmd_docs,
    "scripts":    cmd_scripts,
    "endpoints":  cmd_endpoints,
    "entries":    cmd_entries,
    "parametria": cmd_parametria,
}

# Commands that accept multiple TWX files
MULTI_FILE_COMMANDS = {"cross-model", "is-params"}


def cmd_is_params(args):
    """IS Parameters Report — extracts WebService parameters from multiple TWX files."""
    import glob as _glob

    twx_files: list[str] = list(getattr(args, "twx_files", []) or [])
    search_dir: str | None = getattr(args, "dir", None)
    async_override: list[str] = []
    if getattr(args, "async_list", None):
        async_override = [s.strip() for s in args.async_list.split(",") if s.strip()]

    # ── Resolve files from --dir ──────────────────────────────────────────────
    if search_dir:
        found = sorted(_glob.glob(os.path.join(search_dir, "**", "*.twx"), recursive=True))
        if not found:
            found = sorted(_glob.glob(os.path.join(search_dir, "*.twx")))
        if not found:
            print(f"[ERROR] No .twx files found in: {search_dir}", file=sys.stderr)
            sys.exit(1)
        print(f"\n  📂  Directory: {search_dir}")
        print(f"  📦  TWX files found: {len(found)}")
        for f in found:
            print(f"       · {os.path.basename(f)}")
        twx_files = found

    if not twx_files:
        print("[ERROR] No TWX files to analyze. Use --dir or pass file paths.", file=sys.stderr)
        sys.exit(1)

    output_path = getattr(args, "output", None)
    if not output_path:
        base = os.path.dirname(twx_files[0]) if twx_files else "."
        output_path = os.path.join(base, "is_parameters_report.html")

    print(f"\n  🔍  Analyzing {len(twx_files)} TWX file(s) for IS parameters...\n")

    modules: list[tuple[str, list]] = []
    all_async: list[str] = []

    for twx_path in twx_files:
        # Derive module name from filename:  "Profuturo_Redencion_Bono_AP - foo.twx" → "Redencion Bono"
        fname = os.path.basename(twx_path)
        stem = fname.replace(".twx", "")
        # Strip "Profuturo_" prefix and " - snapshot_name" suffix
        mod_name = stem.split(" - ")[0]
        mod_name = re.sub(r"^Profuturo_", "", mod_name)
        mod_name = mod_name.replace("_AP", "").replace("_", " ").strip()

        try:
            from .twx_parser import TWXParser
            package = TWXParser(twx_path).parse()
            extractor = WebServiceExtractor(package)
            ws_list = extractor.extract()
            n_ops = sum(len(ws.operations) for ws in ws_list)
            print(f"  ✓  {mod_name}: {len(ws_list)} IS · {n_ops} operations")

            if not async_override:
                # Auto-detect Async Tipo 2: a WS where ALL ops are named "respuesta*"
                # is a pure callback receiver (NOV_INSTANCE_MANAGEMENT pattern)
                for ws in ws_list:
                    if not ws.operations:
                        continue
                    all_resp = all(
                        op.name.lower().startswith("respuesta")
                        for op in ws.operations
                    )
                    if all_resp:
                        for op in ws.operations:
                            display = op.process_name or op.name
                            if display not in all_async:
                                all_async.append(display)

            modules.append((mod_name, ws_list))
        except Exception as exc:
            print(f"  ⚠  {mod_name}: {exc}", file=sys.stderr)

    async_names = async_override if async_override else all_async

    total_is = sum(len(ws_list) for _, ws_list in modules)
    total_ops = sum(sum(len(ws.operations) for ws in ws_list) for _, ws_list in modules)

    # ── Extract BPD variables from all TWX files, aggregate unique vars ───────
    all_bpd_vars_raw: list = []
    for twx_path in twx_files:
        try:
            from .twx_parser import TWXParser
            pkg = TWXParser(twx_path).parse()
            bpd_extractor = BPDVariableExtractor(pkg)
            all_bpd_vars_raw.extend(bpd_extractor.extract())
        except Exception:
            pass
    # De-duplicate by name (keep highest frequency entry)
    bpd_by_name: dict[str, object] = {}
    for v in all_bpd_vars_raw:
        key = v.name.lower()
        if key not in bpd_by_name or v.frequency > bpd_by_name[key].frequency:
            bpd_by_name[key] = v
    bpd_vars = sorted(bpd_by_name.values(), key=lambda v: (-v.frequency, v.name))

    print(f"\n  ┌────────────────────────────────────────────┐")
    print(f"  │         IS PARAMETERS — RESULTS            │")
    print(f"  ├────────────────────────────────────────────┤")
    print(f"  │  Modules analyzed    : {len(modules):>4}               │")
    print(f"  │  Integration Services: {total_is:>4}               │")
    print(f"  │  Operations total    : {total_ops:>4}               │")
    print(f"  │  Async Tipo 2 found  : {len(async_names):>4}               │")
    print(f"  │  BPD variables found : {len(bpd_vars):>4}               │")
    print(f"  └────────────────────────────────────────────┘\n")

    html_content = _is_params_generate_html(
        modules=modules,
        async_tipo2=async_names,
        version=__version__,
        bpd_vars=bpd_vars,
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_content, encoding="utf-8")
    print(f"  ✅  HTML report generated: {out}")


def cmd_cross_model(args):
    """Cross-TWX data model pattern analysis."""
    import glob as _glob

    twx_files: list[str] = list(getattr(args, "twx_files", []) or [])
    search_dir: str | None = getattr(args, "dir", None)

    # ── Resolve files from --dir ───────────────────────────────────────────────
    if search_dir:
        found = sorted(_glob.glob(os.path.join(search_dir, "**", "*.twx"), recursive=True))
        if not found:
            found = sorted(_glob.glob(os.path.join(search_dir, "*.twx")))
        if not found:
            print(f"[ERROR] No se encontraron ficheros .twx en: {search_dir}", file=sys.stderr)
            sys.exit(1)
        print(f"\n  📂  Directorio: {search_dir}")
        print(f"  📦  Ficheros .twx encontrados: {len(found)}")
        for f in found:
            print(f"       · {os.path.basename(f)}")
        twx_files = found

    # ── Interactive prompt if nothing was provided ─────────────────────────────
    if not twx_files:
        print("\n  ╔══════════════════════════════════════════════════════╗")
        print("  ║   Cross-TWX Data Model Pattern Analyzer              ║")
        print("  ╚══════════════════════════════════════════════════════╝\n")
        while True:
            user_input = input(
                "  📂  Introduce el path del directorio con los ficheros .twx\n"
                "      (o escribe la ruta a ficheros separados por ';')\n"
                "  ➜  "
            ).strip()
            if not user_input:
                print("  [!] No se introdujo ningún path. Intenta de nuevo.\n")
                continue

            # Check if it's a directory or file list
            if ";" in user_input:
                twx_files = [p.strip() for p in user_input.split(";") if p.strip()]
            elif os.path.isdir(user_input):
                found = sorted(_glob.glob(os.path.join(user_input, "**", "*.twx"), recursive=True))
                if not found:
                    found = sorted(_glob.glob(os.path.join(user_input, "*.twx")))
                if not found:
                    print(f"\n  [!] No se encontraron ficheros .twx en: {user_input}\n")
                    continue
                print(f"\n  📦  Ficheros .twx encontrados: {len(found)}")
                for f in found:
                    print(f"       · {os.path.basename(f)}")
                twx_files = found
            elif os.path.isfile(user_input) and user_input.lower().endswith(".twx"):
                twx_files = [user_input]
            else:
                print(f"\n  [!] No se reconoce como directorio ni fichero .twx: {user_input}\n")
                continue
            break

        # Ask for output path interactively
        if not args.output:
            out_input = input(
                "\n  💾  ¿Dónde guardar el reporte? "
                "(Enter = reporte.html en el directorio de los TWX)\n"
                "  ➜  "
            ).strip()
            if out_input:
                args.output = out_input
            else:
                base = os.path.dirname(twx_files[0]) if twx_files else "."
                args.output = os.path.join(base, "cross_model_report.html")
            print(f"\n  📄  Reporte se guardará en: {args.output}\n")

    if not twx_files:
        print("[ERROR] No hay ficheros .twx para analizar.", file=sys.stderr)
        sys.exit(1)

    # ── Run analysis ───────────────────────────────────────────────────────────
    print(f"\n  🔍  Analizando {len(twx_files)} fichero(s) TWX...\n")
    try:
        analyzer = CrossModelAnalyzer(twx_files)
        report = analyzer.analyze()
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    # ── Print summary to console ───────────────────────────────────────────────
    s = report.stats
    print("  ┌─────────────────────────────────────────────┐")
    print("  │           RESULTADOS DEL ANÁLISIS           │")
    print("  ├─────────────────────────────────────────────┤")
    print(f"  │  Ficheros TWX analizados : {s.get('twx_files_analyzed',0):>4}              │")
    print(f"  │  Business Objects totales: {s.get('total_distinct_bo_names',0):>4}              │")
    print(f"  │  BOs compartidos (≥2 TWX): {s.get('shared_across_files',0):>4}              │")
    print(f"  │    · Idénticos (reusables): {s.get('shared_identical_definition',0):>3}              │")
    print(f"  │    · Divergentes (revisar): {s.get('shared_divergent_definition',0):>3}              │")
    print(f"  │  Clusters estructurales  : {s.get('structural_clusters_found',0):>4}              │")
    print(f"  │  BOs únicos por fichero  : {s.get('unique_to_single_file',0):>4}              │")
    print("  └─────────────────────────────────────────────┘\n")

    # ── Write output ───────────────────────────────────────────────────────────
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ext = output_path.suffix.lower()
        if ext == ".md":
            output_path.write_text(report.to_markdown(), encoding="utf-8")
            fmt = "Markdown"
        elif ext == ".html" or ext == ".htm":
            output_path.write_text(report.to_html(), encoding="utf-8")
            fmt = "HTML"
        else:
            output_path.write_text(
                json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            fmt = "JSON"
        print(f"  ✅  Reporte {fmt} generado: {output_path}")
    else:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))


def main():
    print_banner(version=__version__)

    # Detect if first real arg (after optional flags) is a multi-file command
    raw_args = [a for a in sys.argv[1:] if not a.startswith("-")]
    is_multi = (not raw_args) or (raw_args and raw_args[0] in MULTI_FILE_COMMANDS)

    if is_multi:
        _run_multi_file_command()
    else:
        _run_single_file_command()


def _run_single_file_command():
    parser = argparse.ArgumentParser(
        prog="ibm_twx_tools",
        description=f"{__corporate__} IBM TWX Reverse Engineering Suite v{__version__}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("command", choices=list(COMMANDS.keys()), help="Command to run")
    parser.add_argument("twx_file", help="Path to the .twx file")
    parser.add_argument("-o", "--output", help="Output file path (for docs command)")
    parser.add_argument("-v", "--version", action="version", version=f"{__corporate__} TWX Tools v{__version__}")

    args = parser.parse_args()

    try:
        twx_parser = TWXParser(args.twx_file)
        package = twx_parser.parse()
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)

    COMMANDS[args.command](args, package)


def _run_multi_file_command():
    # Peek at which multi-file command was requested
    raw_args = [a for a in sys.argv[1:] if not a.startswith("-")]
    command = raw_args[0] if raw_args and raw_args[0] in MULTI_FILE_COMMANDS else "cross-model"

    if command == "is-params":
        _run_is_params_command()
    else:
        _run_cross_model_command()


def _run_is_params_command():
    parser = argparse.ArgumentParser(
        prog="ibm_twx_tools is-params",
        description=(
            f"{__corporate__} IBM TWX Reverse Engineering Suite v{__version__}\n"
            "IS Parameters Report — WebService inputs/outputs across N TWX files"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", nargs="?", choices=["is-params"], default="is-params")
    parser.add_argument("twx_files", nargs="*", metavar="twx_file",
                        help="TWX files to analyze (or use --dir)")
    parser.add_argument("-d", "--dir", metavar="DIR",
                        help="Directory containing .twx files")
    parser.add_argument("-o", "--output", default=None,
                        help="Output HTML file (default: is_parameters_report.html in TWX dir)")
    parser.add_argument("--async-list", default=None,
                        help="Comma-separated list of Async Tipo 2 process names (overrides auto-detect)")
    parser.add_argument("-v", "--version", action="version",
                        version=f"{__corporate__} TWX Tools v{__version__}")
    args = parser.parse_args()
    cmd_is_params(args)


def _run_cross_model_command():
    parser = argparse.ArgumentParser(
        prog="ibm_twx_tools cross-model",
        description=(
            f"{__corporate__} IBM TWX Reverse Engineering Suite v{__version__}\n"
            "Cross-TWX Data Model Pattern Analyzer"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", nargs="?", choices=list(MULTI_FILE_COMMANDS),
                        default="cross-model")
    parser.add_argument(
        "twx_files",
        nargs="*",
        metavar="twx_file",
        help="Ficheros .twx a analizar (opcional si se usa --dir o modo interactivo)",
    )
    parser.add_argument(
        "-d", "--dir",
        metavar="DIRECTORIO",
        help="Directorio que contiene los ficheros .twx (los escanea recursivamente)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Fichero de salida: .html (recomendado), .md o .json",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{__corporate__} TWX Tools v{__version__}",
    )

    args = parser.parse_args()
    cmd_cross_model(args)


if __name__ == "__main__":
    main()
