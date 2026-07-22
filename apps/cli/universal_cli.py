#!/usr/bin/env python3
"""
apps/cli/universal_cli.py

Day 37: Universal Compiler CLI Holodeck
Pillar 24: Universal Compiler Groundwork

ADDITIVE ONLY.
This file does NOT modify camera_cli.py.
This file does NOT modify existing engines.
"""

import argparse
import json
import os
import sys


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from packages.core.universal_compiler import (
    compile_universal,
    get_domain_status,
    DOMAIN_ROUTES,
)


def _print_json(payload):
    print(json.dumps(payload, indent=2, default=str, sort_keys=False))


def _generate_universal_dna_safe(prompt):
    try:
        from packages.core.brain import generate_universal_dna
        return generate_universal_dna(prompt)
    except Exception as error:
        return {
            "project_name": "Untitled Reality",
            "domain": "saas",
            "sub_type": "general",
            "required_engines": [],
            "hardware_tier": "potato",
            "target_platform": "web",
            "source": "cli_deterministic_fallback",
            "error": str(error),
        }


def cmd_compile(args):
    project_name = args.project_name

    if not project_name:
        readable_sub_type = args.sub_type.replace("_", " ").title()
        readable_domain = args.domain.title()
        project_name = f"{readable_domain} {readable_sub_type}"

    dna = {
        "project_name": project_name,
        "domain": args.domain,
        "sub_type": args.sub_type,
        "required_engines": [],
        "hardware_tier": "potato",
        "target_platform": "web",
    }

    result = compile_universal(dna)
    _print_json(result)


def cmd_test(args):
    universal_dna = _generate_universal_dna_safe(args.prompt)
    compiled = compile_universal(universal_dna)

    _print_json({
        "prompt": args.prompt,
        "universal_dna": universal_dna,
        "compiled": compiled,
    })


def cmd_domains(args):
    domains = get_domain_status()
    _print_json(domains)


def main():
    parser = argparse.ArgumentParser(
        prog="universal-cli",
        description="Day 37 Universal Compiler Holodeck",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    domain_names = sorted(list(DOMAIN_ROUTES.keys()))

    parser_compile = subparsers.add_parser(
        "compile",
        help="Compile a domain and sub_type into deterministic config JSON.",
    )
    parser_compile.add_argument("domain", choices=domain_names)
    parser_compile.add_argument("sub_type")
    parser_compile.add_argument("--project-name", dest="project_name", default=None)
    parser_compile.set_defaults(func=cmd_compile)

    parser_test = subparsers.add_parser(
        "test",
        help="Test a natural language prompt through the Universal Director.",
    )
    parser_test.add_argument("prompt")
    parser_test.set_defaults(func=cmd_test)

    parser_domains = subparsers.add_parser(
        "domains",
        help="List all available Universal Compiler domains.",
    )
    parser_domains.set_defaults(func=cmd_domains)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()