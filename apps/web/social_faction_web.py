# apps/web/social_faction_web.py

import json
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, render_template_string, request

try:
    from packages.core.models import SocialDNA
    from packages.core.social_engine import SocialMatrixEngine
except ImportError:
    try:
        from core.models import SocialDNA
        from core.social_engine import SocialMatrixEngine
    except ImportError:
        from models import SocialDNA
        from social_engine import SocialMatrixEngine


social_faction_web_bp = Blueprint(
    "social_faction_web",
    __name__,
    url_prefix="/social"
)


# ==========================================================
# DAY 33: DYNAMIC FACTION WEB UI
# ==========================================================
# This is the visual surface for the Social Hole.
#
# The UI does NOT hardcode faction reactions.
# It reads the SocialDNA matrix and renders the mathematical tension.
#
# Flask provides the props.
# React renders the living faction web.
# ==========================================================


DEFAULT_SOCIAL_UI_TOKENS: Dict[str, Any] = {
    "accent_primary": "#38BDF8",
    "background_color": "#0F172A",
    "surface_color": "#111827",
    "panel_color": "#1F2937",
    "text_color": "#E5E7EB",
    "muted_text_color": "#9CA3AF",
    "danger_color": "#EF4444",
    "warning_color": "#F97316",
    "neutral_color": "#94A3B8",
    "positive_color": "#22C55E",
    "strong_positive_color": "#16A34A",
    "spacing_unit": 8,
    "radius": 16,
    "font_family": "Inter, system-ui, sans-serif",
}


def build_demo_social_dna() -> SocialDNA:
    """
    Build a small deterministic society for safe UI testing.
    """
    payload = {
        "factions": [
            {
                "faction_id": "faction_iron_guard",
                "name": "Iron Guard",
                "description": "A militaristic order that values control and protection.",
                "values": ["order", "protection", "discipline"],
                "goals": ["secure the city gates"],
                "disposition_toward_player": 0.1,
            },
            {
                "faction_id": "faction_merchants_guild",
                "name": "Merchants Guild",
                "description": "A trade coalition that values profit and stability.",
                "values": ["profit", "stability", "contracts"],
                "goals": ["control trade routes"],
                "disposition_toward_player": 0.25,
            },
            {
                "faction_id": "faction_ashen_choir",
                "name": "Ashen Choir",
                "description": "A secretive religious movement that values revelation.",
                "values": ["faith", "secrecy", "prophecy"],
                "goals": ["recover ancient relics"],
                "disposition_toward_player": -0.1,
            },
        ],
        "relationship_tensors": [
            {
                "source_id": "faction_iron_guard",
                "target_id": "faction_merchants_guild",
                "weight": -0.55,
                "relationship_type": "rivalry",
                "confidence": 0.9,
                "notes": "The Guard distrusts merchant corruption.",
            },
            {
                "source_id": "faction_merchants_guild",
                "target_id": "faction_iron_guard",
                "weight": -0.45,
                "relationship_type": "rivalry",
                "confidence": 0.85,
                "notes": "The Guild resents Guard tariffs.",
            },
            {
                "source_id": "faction_merchants_guild",
                "target_id": "faction_ashen_choir",
                "weight": 0.35,
                "relationship_type": "cautious_alliance",
                "confidence": 0.7,
                "notes": "The Guild funds Choir relics for profit.",
            },
            {
                "source_id": "faction_ashen_choir",
                "target_id": "faction_iron_guard",
                "weight": -0.65,
                "relationship_type": "religious_tension",
                "confidence": 0.95,
                "notes": "The Choir sees the Guard as spiritually blind.",
            },
            {
                "source_id": "faction_iron_guard",
                "target_id": "player",
                "weight": 0.1,
                "relationship_type": "player_disposition",
                "confidence": 1.0,
                "notes": "The Guard is cautiously neutral toward the player.",
            },
            {
                "source_id": "faction_merchants_guild",
                "target_id": "player",
                "weight": 0.25,
                "relationship_type": "player_disposition",
                "confidence": 1.0,
                "notes": "The Guild sees the player as a useful agent.",
            },
            {
                "source_id": "faction_ashen_choir",
                "target_id": "player",
                "weight": -0.1,
                "relationship_type": "player_disposition",
                "confidence": 1.0,
                "notes": "The Choir is suspicious of the player.",
            },
        ],
        "social_rules": [
            {
                "rule_id": "rule_helping_allies_angers_rivals",
                "trigger_action": "help",
                "effect_type": "disposition_change",
                "magnitude_multiplier": 1.0,
                "description": "Helping a faction irritates its rivals.",
            }
        ],
        "metadata": {
            "demo": True,
            "day": 33,
        },
    }

    return SocialDNA(**payload)


def coerce_social_dna(payload: Optional[Dict[str, Any]]) -> SocialDNA:
    """
    Safely convert incoming JSON into SocialDNA.

    If the payload is invalid, fall back to the demo society.
    """
    if not payload or not isinstance(payload, dict):
        return build_demo_social_dna()

    data = payload.get("social_dna", payload)

    if not isinstance(data, dict):
        return build_demo_social_dna()

    try:
        return SocialDNA(**data)
    except Exception as exc:
        print(f"Social UI fallback engaged: {exc}")
        return build_demo_social_dna()


def build_social_faction_web_props(
    social_dna: SocialDNA,
    title: str = "Faction Web"
) -> Dict[str, Any]:
    """
    Build the UI props consumed by the React Faction Web component.
    """
    tokens = dict(DEFAULT_SOCIAL_UI_TOKENS)

    metadata = getattr(social_dna, "metadata", {}) or {}

    if isinstance(metadata, dict):
        custom_tokens = metadata.get("design_tokens", {})

        if isinstance(custom_tokens, dict):
            tokens.update(custom_tokens)

    if SocialMatrixEngine is None:
        entities = sorted(
            {faction.faction_id for faction in social_dna.factions}
            | {"player"}
        )

        edges = [
            {
                "source_id": relationship.source_id,
                "target_id": relationship.target_id,
                "weight": float(relationship.weight),
                "relationship_type": relationship.relationship_type,
            }
            for relationship in social_dna.relationship_tensors
        ]

        matrix = {
            "entities": entities,
            "matrix": [],
        }

        summary = {
            "entity_count": len(entities),
            "faction_count": len(social_dna.factions),
            "edge_count": len(edges),
            "interaction_block_count": 0,
        }

        interaction_blocks = {}

    else:
        engine = SocialMatrixEngine(social_dna=social_dna)

        entities = engine.get_entity_ids()
        edges = engine.get_edges()
        matrix = engine.get_dense_matrix()
        summary = engine.summary()
        interaction_blocks = engine.get_interaction_blocks()

    factions = []

    for faction in social_dna.factions:
        factions.append(
            {
                "faction_id": faction.faction_id,
                "name": faction.name,
                "description": getattr(faction, "description", ""),
                "values": getattr(faction, "values", []),
                "goals": getattr(faction, "goals", []),
                "disposition_toward_player": float(
                    getattr(faction, "disposition_toward_player", 0.0)
                ),
            }
        )

    return {
        "title": title,
        "tokens": tokens,
        "entities": entities,
        "factions": factions,
        "edges": edges,
        "matrix": matrix,
        "summary": summary,
        "interaction_blocks": interaction_blocks,
        "player_id": "player",
    }


SOCIAL_FACTION_WEB_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Social Matrix — Faction Web</title>

    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>

    <style>
      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        background: #0f172a;
        color: #e5e7eb;
        font-family: Inter, system-ui, sans-serif;
      }

      #root {
        min-height: 100vh;
      }

      .app-shell {
        min-height: 100vh;
        padding: 24px;
      }

      .app-header {
        margin-bottom: 16px;
      }

      .app-title {
        margin: 0;
        font-size: 28px;
        font-weight: 800;
      }

      .app-subtitle {
        margin: 6px 0 0;
        color: #9ca3af;
        font-size: 14px;
      }

      .layout {
        display: flex;
        gap: 16px;
        align-items: stretch;
      }

      .canvas-panel {
        flex: 2;
        min-height: 560px;
        border-radius: 18px;
        background: rgba(17, 24, 39, 0.92);
        border: 1px solid rgba(148, 163, 184, 0.16);
        overflow: hidden;
      }

      .side-panel {
        flex: 1;
        min-width: 300px;
        border-radius: 18px;
        background: rgba(31, 41, 55, 0.92);
        border: 1px solid rgba(148, 163, 184, 0.16);
        padding: 16px;
        overflow: auto;
        max-height: 720px;
      }

      .panel-title {
        margin: 0 0 10px;
        font-size: 18px;
        font-weight: 700;
      }

      .muted {
        color: #9ca3af;
        font-size: 13px;
      }

      .card {
        background: rgba(17, 24, 39, 0.72);
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 14px;
        padding: 12px;
        margin-bottom: 12px;
      }

      .row {
        display: flex;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 6px;
      }

      .pill {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 999px;
        font-size: 12px;
        background: rgba(148, 163, 184, 0.14);
        color: #e5e7eb;
      }

      .relation-item {
        margin-bottom: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.12);
      }

      .relation-item:last-child {
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
      }

      .meter-track {
        width: 100%;
        height: 10px;
        border-radius: 999px;
        background: rgba(148, 163, 184, 0.16);
        overflow: hidden;
        margin-top: 6px;
      }

      .meter-fill {
        height: 100%;
        border-radius: 999px;
      }

      .empty-state {
        color: #9ca3af;
        font-size: 14px;
      }

      svg {
        width: 100%;
        height: 100%;
        display: block;
      }

      .node-label {
        font-size: 13px;
        fill: #e5e7eb;
        user-select: none;
      }

      .node-sublabel {
        font-size: 11px;
        fill: #9ca3af;
        user-select: none;
      }

      @media (max-width: 980px) {
        .layout {
          flex-direction: column;
        }

        .side-panel {
          max-height: none;
        }
      }
    </style>
  </head>

  <body>
    <div id="root"></div>

    <script>
      window.__SOCIAL_FACTION_WEB_PROPS__ = {{ props_json|safe }};

      const e = React.createElement;

      function clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
      }

      function formatWeight(weight) {
        return Number(weight || 0).toFixed(2);
      }

      function weightColor(weight, tokens) {
        const w = Number(weight || 0);

        if (w <= -0.6) return tokens.danger_color || "#ef4444";
        if (w <= -0.2) return tokens.warning_color || "#f97316";
        if (w < 0.2) return tokens.neutral_color || "#94a3b8";
        if (w < 0.6) return tokens.positive_color || "#22c55e";

        return tokens.strong_positive_color || "#16a34a";
      }

      function entityLabel(entityId, factions) {
        const faction = factions.find((f) => f.faction_id === entityId);

        if (faction) {
          return faction.name;
        }

        if (entityId === "player") {
          return "Player";
        }

        return entityId
          .replace(/_/g, " ")
          .replace(/\b\w/g, (char) => char.toUpperCase());
      }

      functionDispositionMeter(value, tokens) {
        const normalized = clamp((Number(value || 0) + 1) / 2, 0, 1);
        const width = Math.round(normalized * 100);
        const color = weightColor(value, tokens);

        return e(
          "div",
          { className: "meter-track" },
          e("div", {
            className: "meter-fill",
            style: {
              width: width + "%",
              background: color,
            },
          })
        );
      }

      function RelationList({ title, relations, tokens, factions }) {
        if (!relations || relations.length === 0) {
          return e(
            "div",
            { className: "card" },
            e("div", { className: "panel-title" }, title),
            e("div", { className: "empty-state" }, "No relationships.")
          );
        }

        return e(
          "div",
          { className: "card" },
          e("div", { className: "panel-title" }, title),
          relations.map((relation, index) => {
            const color = weightColor(relation.weight, tokens);

            return e(
              "div",
              { className: "relation-item", key: index },
              e(
                "div",
                { className: "row" },
                e("strong", null, entityLabel(relation.target_id || relation.source_id, factions)),
                e("span", { className: "pill", style: { background: color + "22", color } }, formatWeight(relation.weight))
              ),
              e(
                "div",
                { className: "muted" },
                relation.relationship_type || "neutral"
              ),
              dispositionMeter(relation.weight, tokens)
            );
          })
        );
      }

      function FactionWebSVG({ props, selected, setSelected }) {
        const tokens = props.tokens || {};
        const entities = props.entities || [];
        const edges = props.edges || [];
        const factions = props.factions || [];

        const width = 960;
        const height = 620;
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = 210;

        const positions = React.useMemo(() => {
          const result = {};

          entities.forEach((entityId, index) => {
            const angle = (index / Math.max(entities.length, 1)) * Math.PI * 2;

            result[entityId] = {
              x: centerX + radius * Math.cos(angle),
              y: centerY + radius * Math.sin(angle),
            };
          });

          return result;
        }, [entities]);

        if (!entities.length) {
          return e(
            "div",
            { className: "canvas-panel", style: { display: "grid", placeItems: "center" } },
            e("div", { className: "empty-state" }, "No social entities discovered yet.")
          );
        }

        return e(
          "div",
          { className: "canvas-panel" },
          e(
            "svg",
            {
              viewBox: `0 0 ${width} ${height}`,
              role: "img",
              "aria-label": "Faction relationship web",
            },
            edges.map((edge, index) => {
              const source = positions[edge.source_id];
              const target = positions[edge.target_id];

              if (!source || !target) {
                return null;
              }

              const involvesSelected =
                !selected ||
                edge.source_id === selected ||
                edge.target_id === selected;

              const color = weightColor(edge.weight, tokens);
              const absWeight = Math.abs(Number(edge.weight || 0));

              return e("line", {
                key: `edge-${index}`,
                x1: source.x,
                y1: source.y,
                x2: target.x,
                y2: target.y,
                stroke: color,
                strokeWidth: 1 + absWeight * 5,
                strokeOpacity: involvesSelected ? 0.28 + absWeight * 0.66 : 0.06,
                strokeLinecap: "round",
              });
            }),
            entities.map((entityId) => {
              const pos = positions[entityId];

              if (!pos) {
                return null;
              }

              const isSelected = selected === entityId;
              const isPlayer = entityId === (props.player_id || "player");

              const faction = factions.find((f) => f.faction_id === entityId);
              const disposition = faction
                ? faction.disposition_toward_player
                : entityId === props.player_id
                ? 1
                : 0;

              const fill = isPlayer
                ? tokens.accent_primary || "#38bdf8"
                : weightColor(disposition, tokens);

              return e(
                "g",
                {
                  key: entityId,
                  onClick: () => setSelected(isSelected ? null : entityId),
                  style: { cursor: "pointer" },
                },
                e("circle", {
                  cx: pos.x,
                  cy: pos.y,
                  r: isSelected ? 26 : 20,
                  fill: fill,
                  stroke: isSelected ? "#ffffff" : "rgba(255,255,255,0.22)",
                  strokeWidth: isSelected ? 3 : 1.5,
                  opacity: selected && !isSelected ? 0.55 : 1,
                }),
                e(
                  "text",
                  {
                    x: pos.x,
                    y: pos.y + 40,
                    textAnchor: "middle",
                    className: "node-label",
                    opacity: selected && !isSelected ? 0.55 : 1,
                  },
                  entityLabel(entityId, factions)
                ),
                e(
                  "text",
                  {
                    x: pos.x,
                    y: pos.y + 56,
                    textAnchor: "middle",
                    className: "node-sublabel",
                    opacity: selected && !isSelected ? 0.45 : 0.9,
                  },
                  isPlayer ? "observer" : entityId
                )
              );
            })
          )
        );
      }

      function SocialFactionWeb(props) {
        const [selected, setSelected] = React.useState(null);

        const tokens = props.tokens || {};
        const summary = props.summary || {};
        const factions = props.factions || [];
        const edges = props.edges || [];
        const interactionBlocks = props.interaction_blocks || {};

        const outgoing = selected
          ? edges.filter((edge) => edge.source_id === selected)
          : [];

        const incoming = selected
          ? edges.filter((edge) => edge.target_id === selected)
          : [];

        const selectedRefusals = selected
          ? interactionBlocks[selected] || []
          : [];

        const refusedBy = selected
          ? Object.keys(interactionBlocks).filter((sourceId) =>
              (interactionBlocks[sourceId] || []).includes(selected)
            )
          : [];

        const shellStyle = {
          background: tokens.background_color || "#0f172a",
          color: tokens.text_color || "#e5e7eb",
          fontFamily: tokens.font_family || "Inter, system-ui, sans-serif",
        };

        return e(
          "div",
          { className: "app-shell", style: shellStyle },
          e(
            "header",
            { className: "app-header" },
            e("h1", { className: "app-title" }, props.title || "Faction Web"),
            e(
              "p",
              { className: "app-subtitle" },
              `Entities: ${summary.entity_count || 0} | ` +
              `Factions: ${summary.faction_count || 0} | ` +
              `Relationships: ${summary.edge_count || 0} | ` +
              `Refusals: ${summary.interaction_block_count || 0}`
            )
          ),
          e(
            "div",
            { className: "layout" },
            e(FactionWebSVG, { props, selected, setSelected }),
            e(
              "aside",
              { className: "side-panel" },
              e("h2", { className: "panel-title" }, "Social Inspector"),
              selected
                ? e(
                    "div",
                    { className: "card" },
                    e("strong", null, entityLabel(selected, factions)),
                    e("div", { className: "muted" }, selected),
                    selectedRefusals.length > 0
                      ? e(
                          "div",
                          { style: { marginTop: "10px" } },
                          e("span", { className: "pill", style: { background: "#ef444422", color: "#ef4444" } }, "Refuses interaction with:"),
                          e("div", { className: "muted", style: { marginTop: "6px" } }, selectedRefusals.join(", "))
                        )
                      : null,
                    refusedBy.length > 0
                      ? e(
                          "div",
                          { style: { marginTop: "10px" } },
                          e("span", { className: "pill", style: { background: "#f9731622", color: "#f97316" } }, "Interaction refused by:"),
                          e("div", { className: "muted", style: { marginTop: "6px" } }, refusedBy.join(", "))
                        )
                      : null
                  )
                : e(
                    "div",
                    { className: "card" },
                    e("div", { className: "empty-state" }, "Select a node to inspect its social tension.")
                  ),
              e(RelationList, {
                title: selected ? "Outgoing Relationships" : "Outgoing Relationships",
                relations: outgoing,
                tokens,
                factions,
              }),
              e(RelationList, {
                title: "Incoming Relationships",
                relations: incoming,
                tokens,
                factions,
              }),
              e(
                "div",
                { className: "card" },
                e("div", { className: "panel-title" }, "Faction Dispositions Toward Player"),
                factions.length === 0
                  ? e("div", { className: "empty-state" }, "No factions discovered yet.")
                  : factions.map((faction) =>
                      e(
                        "div",
                        { className: "relation-item", key: faction.faction_id },
                        e(
                          "div",
                          { className: "row" },
                          e("strong", null, faction.name),
                          e(
                            "span",
                            {
                              className: "pill",
                              style: {
                                background:
                                  weightColor(faction.disposition_toward_player, tokens) + "22",
                                color: weightColor(faction.disposition_toward_player, tokens),
                              },
                            },
                            formatWeight(faction.disposition_toward_player)
                          )
                        ),
                        dispositionMeter(faction.disposition_toward_player, tokens)
                      )
                    )
              )
            )
          )
        );
      }

      const root = ReactDOM.createRoot(document.getElementById("root"));
      root.render(e(SocialFactionWeb, window.__SOCIAL_FACTION_WEB_PROPS__));
    </script>
  </body>
</html>
"""


@social_faction_web_bp.route("/faction-web", methods=["GET"])
def social_faction_web_page():
    """
    Render the Dynamic Faction Web UI.

    By default, this uses a safe demo society.
    Later, we can connect it to the active Supabase social_matrices row.
    """
    social_dna = build_demo_social_dna()
    props = build_social_faction_web_props(social_dna)

    props_json = json.dumps(props, default=str).replace("<", "\\u003c")

    return render_template_string(
        SOCIAL_FACTION_WEB_TEMPLATE,
        props_json=props_json
    )


@social_faction_web_bp.route("/faction-web/props", methods=["POST"])
def social_faction_web_props():
    """
    API hook for the UI Synthesizer.

    Send JSON:
    {
      "social_dna": { ...SocialDNA... }
    }

    Or send the SocialDNA object directly.

    Returns UI props for the React Faction Web component.
    """
    payload = request.get_json(silent=True) or {}
    social_dna = coerce_social_dna(payload)
    props = build_social_faction_web_props(social_dna)

    return jsonify(props)