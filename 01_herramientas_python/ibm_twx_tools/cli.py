"""
NTTDATA IBM TWX Reverse Engineering Suite — CLI
================================================
Usage:
    python -m ibm_twx_tools <command> <file.twx> [options]

Commands:
    analyze    Full analysis summary
    entities   Extract Business Objects
    services   Extract services and scripts
    flows      Map process flows (Mermaid)
    deps       Dependency call graph
    docs       Generate full Markdown documentation
    scripts    Dump all embedded scripts
    endpoints  List all external endpoints
    entries    Show entry points
"""

import argparse
import json
import sys
import os
from pathlib import Path

from . import __version__, __corporate__, __product__
from .twx_parser import TWXParser
from .entity_extractor import EntityExtractor
from .service_extractor import ServiceExtractor
from .flow_mapper import FlowMapper
from .doc_generator import DocGenerator
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


COMMANDS = {
    "analyze":   cmd_analyze,
    "entities":  cmd_entities,
    "services":  cmd_services,
    "flows":     cmd_flows,
    "deps":      cmd_deps,
    "docs":      cmd_docs,
    "scripts":   cmd_scripts,
    "endpoints": cmd_endpoints,
    "entries":   cmd_entries,
}


def main():
    print_banner(version=__version__)

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


if __name__ == "__main__":
    main()
