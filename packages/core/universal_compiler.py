"""
packages/core/universal_compiler.py

Day 37: Universal Application Compiler Core
Pillar 24: Universal Compiler Groundwork

This file is additive.
It does NOT modify existing engine files.
It only routes ontological intent into deterministic engine configuration.
"""

try:
    from .models import UniversalDNA, DomainRoute
except ImportError:
    try:
        from packages.core.models import UniversalDNA, DomainRoute
    except ImportError:
        from models import UniversalDNA, DomainRoute


UNIVERSAL_COMPILER_VERSION = "0.1.0"
DEFAULT_FALLBACK_DOMAIN = "saas"


DOMAIN_ROUTES = {
    "game": {
        "required_engines": [
            "genesis_renderer",
            "ecs",
            "physics",
            "audio",
            "input",
            "navigation",
            "ecology",
            "social",
            "narrative",
            "economy",
            "flow",
            "content_weaver",
            "fidelity",
            "cinematographer",
        ],
        "template_vault": "game_templates",
    },
    "saas": {
        "required_engines": [
            "ui_synthesizer",
            "backend_compiler",
            "security",
            "deployment",
            "localization",
            "accessibility",
        ],
        "template_vault": "saas_templates",
    },
    "desktop": {
        "required_engines": [
            "ui_synthesizer",
            "backend_compiler",
            "deployment",
            "input",
        ],
        "template_vault": "desktop_templates",
    },
    "mobile": {
        "required_engines": [
            "ui_synthesizer",
            "backend_compiler",
            "deployment",
            "accessibility",
        ],
        "template_vault": "mobile_templates",
    },
    "vr": {
        "required_engines": [
            "genesis_renderer",
            "ecs",
            "physics",
            "audio",
            "input",
            "fidelity",
            "sensory",
        ],
        "template_vault": "vr_templates",
    },
    "film": {
        "required_engines": [
            "genesis_renderer",
            "cinematographer",
            "audio",
            "fidelity",
            "content_weaver",
        ],
        "template_vault": "film_templates",
    },
    "science": {
        "required_engines": [
            "ecs",
            "fidelity",
            "telemetry",
            "deployment",
        ],
        "template_vault": "science_templates",
    },
    "music": {
        "required_engines": [
            "audio",
            "input",
            "ui_synthesizer",
        ],
        "template_vault": "music_templates",
    },
    "architecture": {
        "required_engines": [
            "genesis_renderer",
            "fidelity",
            "ui_synthesizer",
        ],
        "template_vault": "architecture_templates",
    },
    "education": {
        "required_engines": [
            "tutorial",
            "flow",
            "ui_synthesizer",
            "narrative",
            "accessibility",
        ],
        "template_vault": "education_templates",
    },
}


DOMAIN_STATUS = {
    "game": "working",
    "saas": "working",
    "desktop": "hook",
    "mobile": "hook",
    "vr": "hook",
    "film": "hook",
    "science": "hook",
    "music": "hook",
    "architecture": "hook",
    "education": "hook",
}


DOMAIN_HOOKS = {
    "desktop": {"planned_phase": "Phase 5 (Days 1461-1825)"},
    "mobile": {"planned_phase": "Phase 5 (Days 1461-1825)"},
    "vr": {"planned_phase": "Phase 7 (Days 2191-2555)"},
    "film": {"planned_phase": "Phase 6 (Days 1826-2190)"},
    "science": {"planned_phase": "Phase 8 (Days 2556-2920)"},
    "music": {"planned_phase": "Phase 6 (Days 1826-2190)"},
    "architecture": {"planned_phase": "Phase 7 (Days 2191-2555)"},
    "education": {"planned_phase": "Phase 5 (Days 1461-1825)"},
}


def _to_dict(model):
    if model is None:
        return None

    if hasattr(model, "model_dump"):
        return model.model_dump()

    if hasattr(model, "dict"):
        return model.dict()

    return model


def _safe_enum_value(value, default_value):
    if value is None:
        return default_value

    if hasattr(value, "value"):
        return str(value.value)

    return str(value)


def _extract_design_tokens(dna):
    return _to_dict(getattr(dna, "design_tokens", None))


def resolve_domain(dna):
    if isinstance(dna, dict):
        dna = UniversalDNA(**dna)

    domain_value = _safe_enum_value(
        getattr(dna, "domain", DEFAULT_FALLBACK_DOMAIN),
        DEFAULT_FALLBACK_DOMAIN
    ).lower()

    sub_type = getattr(dna, "sub_type", "general") or "general"

    fallback_domain = None

    if domain_value not in DOMAIN_ROUTES:
        fallback_domain = DEFAULT_FALLBACK_DOMAIN
        domain_value = DEFAULT_FALLBACK_DOMAIN

    route = DOMAIN_ROUTES[domain_value]
    resolved_engines = list(route["required_engines"])

    return DomainRoute(
        domain=domain_value,
        sub_type=sub_type,
        resolved_engines=resolved_engines,
        template_vault=route["template_vault"],
        estimated_compile_ms=float(len(resolved_engines) * 7.0),
        fallback_domain=fallback_domain,
    )


GAME_SUBTYPE_PROFILES = {
    "open_world_rpg": {
        "genesis": "biome_heavy",
        "ecs": "npc_dense",
        "physics": "full",
        "narrative": "branching",
        "economy": "complex",
        "fidelity": 3,
        "camera": "third_person",
        "navigation": "navmesh",
        "ecology": True,
        "social": True,
        "cinematographer": "cinematic",
    },
    "fps": {
        "genesis": "arena",
        "ecs": "combat",
        "physics": "full",
        "narrative": "linear",
        "economy": "simple",
        "fidelity": 4,
        "camera": "first_person",
        "navigation": "navmesh",
        "ecology": False,
        "social": True,
        "cinematographer": "action",
    },
    "puzzle": {
        "genesis": "minimal",
        "ecs": "logic",
        "physics": "simplified",
        "narrative": "environmental",
        "economy": "none",
        "fidelity": 2,
        "camera": "isometric",
        "navigation": "none",
        "ecology": False,
        "social": False,
        "cinematographer": "static",
    },
    "strategy": {
        "genesis": "grid",
        "ecs": "army",
        "physics": "minimal",
        "narrative": "campaign",
        "economy": "complex",
        "fidelity": 2,
        "camera": "top_down",
        "navigation": "grid",
        "ecology": True,
        "social": True,
        "cinematographer": "strategic",
    },
    "platformer": {
        "genesis": "level_based",
        "ecs": "actor",
        "physics": "full",
        "narrative": "linear",
        "economy": "simple",
        "fidelity": 3,
        "camera": "side_scroller",
        "navigation": "path",
        "ecology": False,
        "social": False,
        "cinematographer": "gameplay",
    },
    "default": {
        "genesis": "minimal",
        "ecs": "general",
        "physics": "simplified",
        "narrative": "linear",
        "economy": "simple",
        "fidelity": 2,
        "camera": "third_person",
        "navigation": "auto",
        "ecology": False,
        "social": False,
        "cinematographer": "gameplay",
    },
}


def compile_game_domain(dna):
    if isinstance(dna, dict):
        dna = UniversalDNA(**dna)

    project_name = getattr(dna, "project_name", "Untitled Reality")
    sub_type = str(getattr(dna, "sub_type", "general") or "general").lower().strip().replace(" ", "_")
    profile = GAME_SUBTYPE_PROFILES.get(sub_type, GAME_SUBTYPE_PROFILES["default"])

    hardware_value = _safe_enum_value(getattr(dna, "hardware_tier", None), "potato")
    platform_value = _safe_enum_value(getattr(dna, "target_platform", None), "web")

    requested_fidelity = int(profile.get("fidelity", 2))

    if hardware_value == "potato":
        resolved_fidelity = min(requested_fidelity, 2)
    elif hardware_value == "mid":
        resolved_fidelity = min(requested_fidelity, 3)
    else:
        resolved_fidelity = requested_fidelity

    game_route = resolve_domain({
        "project_name": project_name,
        "domain": "game",
        "sub_type": sub_type,
        "hardware_tier": hardware_value,
        "target_platform": platform_value,
    })

    return {
        "schema": "ogf.game.config/v1",
        "compiler": "universal_compiler",
        "compiler_version": UNIVERSAL_COMPILER_VERSION,
        "project_name": project_name,
        "domain": "game",
        "sub_type": sub_type,
        "route": _to_dict(game_route),
        "design_tokens": _extract_design_tokens(dna),
        "engine_config": {
            "genesis_renderer": {
                "mode": profile["genesis"],
                "hardware_tier": hardware_value,
                "target_platform": platform_value,
            },
            "ecs": {"density": profile["ecs"]},
            "physics": {"mode": profile["physics"]},
            "narrative": {"structure": profile["narrative"]},
            "economy": {"complexity": profile["economy"]},
            "fidelity": {
                "requested_level": requested_fidelity,
                "resolved_level": resolved_fidelity,
                "hardware_tier": hardware_value,
            },
            "camera": {"mode": profile["camera"]},
            "navigation": {"mode": profile["navigation"]},
            "audio": {"mode": "procedural", "dsp": "enabled"},
            "input": {"mode": "deterministic"},
            "ecology": {"enabled": profile["ecology"]},
            "social": {"enabled": profile["social"]},
            "flow": {"enabled": True},
            "content_weaver": {"enabled": True},
            "cinematographer": {"mode": profile["cinematographer"]},
        },
        "deterministic": True,
        "raw_code": False,
    }


SAAS_SUBTYPE_PROFILES = {
    "project_management": {
        "entity_name": "Project",
        "entities": ["Project", "Task", "User"],
        "components": ["KanbanBoard", "Calendar", "DataGrid"],
        "routes": [
            {"method": "POST", "path": "/projects"},
            {"method": "POST", "path": "/tasks"},
            {"method": "PATCH", "path": "/tasks/status"},
            {"method": "GET", "path": "/projects"},
        ],
        "auth_type": "JWT",
        "database_schema": "projects_tasks_users",
    },
    "crm": {
        "entity_name": "Contact",
        "entities": ["Contact", "Company", "Deal", "Activity"],
        "components": ["DataTable", "PipelineBoard", "ContactForm", "ActivityTimeline"],
        "routes": [
            {"method": "POST", "path": "/contacts"},
            {"method": "POST", "path": "/deals"},
            {"method": "PATCH", "path": "/deals"},
            {"method": "POST", "path": "/activities"},
            {"method": "GET", "path": "/contacts"},
        ],
        "auth_type": "JWT",
        "database_schema": "crm_contacts_deals_activities",
    },
    "analytics_dashboard": {
        "entity_name": "Metric",
        "entities": ["Metric", "Chart", "Report"],
        "components": ["LineChart", "BarChart", "DataTable", "FilterPanel"],
        "routes": [
            {"method": "GET", "path": "/metrics"},
            {"method": "POST", "path": "/reports"},
            {"method": "GET", "path": "/reports"},
        ],
        "auth_type": "OAuth",
        "database_schema": "metrics_reports",
    },
    "e_commerce": {
        "entity_name": "Product",
        "entities": ["Product", "Cart", "Order", "Customer"],
        "components": ["ProductGrid", "CartDrawer", "CheckoutForm", "OrderTable"],
        "routes": [
            {"method": "GET", "path": "/products"},
            {"method": "POST", "path": "/cart"},
            {"method": "POST", "path": "/checkout"},
            {"method": "GET", "path": "/orders"},
        ],
        "auth_type": "JWT",
        "database_schema": "commerce_products_orders_customers",
    },
    "default": {
        "entity_name": "Item",
        "entities": ["Item", "User"],
        "components": ["DataTable", "Form", "Button"],
        "routes": [
            {"method": "GET", "path": "/items"},
            {"method": "POST", "path": "/items"},
        ],
        "auth_type": "JWT",
        "database_schema": "items_users",
    },
}


def compile_saas_domain(dna):
    if isinstance(dna, dict):
        dna = UniversalDNA(**dna)

    project_name = getattr(dna, "project_name", "Untitled Reality")
    sub_type = str(getattr(dna, "sub_type", "general") or "general").lower().strip().replace(" ", "_")
    profile = SAAS_SUBTYPE_PROFILES.get(sub_type, SAAS_SUBTYPE_PROFILES["default"])

    hardware_value = _safe_enum_value(getattr(dna, "hardware_tier", None), "potato")
    platform_value = _safe_enum_value(getattr(dna, "target_platform", None), "web")

    saas_route = resolve_domain({
        "project_name": project_name,
        "domain": "saas",
        "sub_type": sub_type,
        "hardware_tier": hardware_value,
        "target_platform": platform_value,
    })

    required_components = []
    for component_name in profile["components"]:
        required_components.append({
            "component_name": component_name,
            "props": {},
        })

    return {
        "schema": "ogf.saas.app.config/v1",
        "compiler": "universal_compiler",
        "compiler_version": UNIVERSAL_COMPILER_VERSION,
        "project_name": project_name,
        "domain": "saas",
        "sub_type": sub_type,
        "route": _to_dict(saas_route),
        "design_tokens": _extract_design_tokens(dna),
        "app_dna": {
            "app_name": project_name,
            "version": "0.1.0",
            "entity_name": profile["entity_name"],
            "entities": profile["entities"],
            "required_components": required_components,
            "design_tokens": _extract_design_tokens(dna),
            "hardware_tier": hardware_value,
            "target_platform": platform_value,
        },
        "logic_dna": {
            "entity_name": profile["entity_name"],
            "routes": profile["routes"],
            "auth_type": profile["auth_type"],
            "database_schema": profile["database_schema"],
        },
        "deterministic": True,
        "raw_code": False,
    }


def _domain_hook_payload(domain_value, dna, fallback_config=None):
    if isinstance(dna, dict):
        dna = UniversalDNA(**dna)

    hook = DOMAIN_HOOKS.get(domain_value, {})
    route = resolve_domain(dna)

    return {
        "schema": "ogf.universal.domain.hook/v1",
        "compiler": "universal_compiler",
        "compiler_version": UNIVERSAL_COMPILER_VERSION,
        "domain": domain_value,
        "sub_type": getattr(dna, "sub_type", "general") or "general",
        "status": "not_yet_implemented",
        "fallback": DEFAULT_FALLBACK_DOMAIN,
        "planned_phase": hook.get("planned_phase", "Phase 7 (Days 2191-2555)"),
        "route": _to_dict(route),
        "fallback_config": fallback_config,
        "deterministic": True,
        "raw_code": False,
    }


def compile_desktop_hook(dna):
    return _domain_hook_payload("desktop", dna, compile_saas_domain(dna))


def compile_mobile_hook(dna):
    return _domain_hook_payload("mobile", dna, compile_saas_domain(dna))


def compile_vr_hook(dna):
    return _domain_hook_payload("vr", dna, compile_saas_domain(dna))


def compile_film_hook(dna):
    return _domain_hook_payload("film", dna, compile_saas_domain(dna))


def compile_science_hook(dna):
    return _domain_hook_payload("science", dna, compile_saas_domain(dna))


def compile_music_hook(dna):
    return _domain_hook_payload("music", dna, compile_saas_domain(dna))


def compile_architecture_hook(dna):
    return _domain_hook_payload("architecture", dna, compile_saas_domain(dna))


def compile_education_hook(dna):
    return _domain_hook_payload("education", dna, compile_saas_domain(dna))


def compile_universal(dna):
    if isinstance(dna, dict):
        dna = UniversalDNA(**dna)

    route = resolve_domain(dna)

    if route.domain == "game":
        return compile_game_domain(dna)

    if route.domain == "saas":
        return compile_saas_domain(dna)

    fallback_config = compile_saas_domain(dna)

    return _domain_hook_payload(
        route.domain,
        dna,
        fallback_config
    )


def get_domain_status():
    status_list = []

    for domain_name, route in DOMAIN_ROUTES.items():
        status_list.append({
            "domain": domain_name,
            "status": DOMAIN_STATUS.get(domain_name, "hook"),
            "required_engines": list(route["required_engines"]),
            "template_vault": route["template_vault"],
        })

    return status_list