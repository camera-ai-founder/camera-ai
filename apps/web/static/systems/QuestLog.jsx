// ==========================================================
// DAY 32 STEP 6: THE DYNAMIC QUEST LOG
// File: apps/web/static/systems/QuestLog.jsx
// ==========================================================
// This component reads QuestDNA from the Flask API and renders
// the story graph using Day 10 Atomic Tokens.
//
// It NEVER reads raw dialogue.
// It NEVER reads hardcoded scripts.
// It only reads semantic QuestDNA.
//
// Usage example:
//
// import QuestLog from "./static/systems/QuestLog.jsx";
//
// <QuestLog
//   projectId="YOUR_PROJECT_UUID"
//   completedNodeIds={["node_enter_ruins"]}
//   refreshKey={0}
// />
//
// If projectId is empty, the API will automatically use the
// latest project from Supabase.
// ==========================================================

import React, { useEffect, useState } from "react";

export default function QuestLog({
  projectId = "",
  completedNodeIds = [],
  refreshKey = 0
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const safeCompletedNodeIds = Array.isArray(completedNodeIds)
    ? completedNodeIds
    : [];

  useEffect(() => {
    const controller = new AbortController();

    async function loadQuestLog() {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams();

        if (projectId) {
          params.set("project_id", projectId);
        }

        if (safeCompletedNodeIds.length > 0) {
          params.set("completed", safeCompletedNodeIds.join(","));
        }

        const queryString = params.toString();
        const url = queryString
          ? `/api/quest-log?${queryString}`
          : "/api/quest-log";

        const response = await fetch(url, {
          signal: controller.signal
        });

        const payload = await response.json();

        if (!response.ok || !payload.success) {
          throw new Error(
            payload.errors && payload.errors.length > 0
              ? payload.errors.join(" ")
              : "Quest Log failed to load."
          );
        }

        setData(payload);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message);
        }
      } finally {
        setLoading(false);
      }
    }

    loadQuestLog();

    return () => {
      controller.abort();
    };
  }, [
    projectId,
    safeCompletedNodeIds.join("|"),
    refreshKey
  ]);

  if (loading) {
    return (
      <div style={styles.loadingRoot}>
        <div style={styles.loadingText}>
          Quest Log synchronizing...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.errorRoot}>
        <div style={styles.errorTitle}>
          Quest Log Error
        </div>

        <div style={styles.errorMessage}>
          {error}
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const tokens = data.tokens || {};

  return (
    <section style={styles.root(tokens)}>
      <header style={styles.header(tokens)}>
        <div style={styles.title(tokens)}>
          Quest Log
        </div>

        <div style={styles.questId(tokens)}>
          {data.quest_id}
        </div>
      </header>

      <div style={styles.nodeList(tokens)}>
        {data.nodes.map((node, index) => {
          return (
            <article
              key={node.node_id}
              style={styles.nodeCard(tokens, node)}
            >
              <div style={styles.nodeTopRow(tokens)}>
                <div style={styles.nodeIndex(tokens)}>
                  {index + 1}
                </div>

                <div style={styles.nodeConcept(tokens, node)}>
                  {node.semantic_concept}
                </div>

                {node.is_active && (
                  <span style={styles.activeBadge(tokens)}>
                    ACTIVE
                  </span>
                )}

                {node.is_completed && (
                  <span style={styles.completedBadge(tokens)}>
                    COMPLETE
                  </span>
                )}

                {node.is_locked && (
                  <span style={styles.lockedBadge(tokens)}>
                    LOCKED
                  </span>
                )}
              </div>

              <div style={styles.nodeMeta(tokens)}>
                <span style={styles.nodeId(tokens)}>
                  {node.node_id}
                </span>

                {node.is_active && (
                  <span style={styles.activeHint(tokens)}>
                    This story node is currently unlocked.
                  </span>
                )}

                {node.is_locked && (
                  <span style={styles.lockedHint(tokens)}>
                    Complete prerequisite nodes to unlock this beat.
                  </span>
                )}

                {node.is_completed && (
                  <span style={styles.completedHint(tokens)}>
                    This story beat has already changed the world.
                  </span>
                )}
              </div>
            </article>
          );
        })}
      </div>

      <footer style={styles.footer(tokens)}>
        <div style={styles.footerLabel(tokens)}>
          Narrative Graph Edges
        </div>

        <div style={styles.edgeList(tokens)}>
          {data.edges.length === 0 && (
            <div style={styles.emptyEdge(tokens)}>
              No directed edges.
            </div>
          )}

          {data.edges.map((edge, index) => {
            return (
              <div
                key={`${edge.from_node}->${edge.to_node}-${index}`}
                style={styles.edgeItem(tokens)}
              >
                <span style={styles.edgeNode(tokens)}>
                  {edge.from_node}
                </span>

                <span style={styles.edgeArrow(tokens)}>
                  →
                </span>

                <span style={styles.edgeNode(tokens)}>
                  {edge.to_node}
                </span>
              </div>
            );
          })}
        </div>
      </footer>
    </section>
  );
}

const styles = {
  root: (tokens) => ({
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacing_unit ? tokens.spacing_unit * 2 : 16,
    background: tokens.surface_color || "#111827",
    color: tokens.text_color || "#E2E8F0",
    borderRadius: tokens.radius || 12,
    border: `${tokens.border_width || 1}px solid rgba(148, 163, 184, 0.2)`,
    padding: tokens.spacing_unit ? tokens.spacing_unit * 3 : 24,
    fontFamily: "Inter, system-ui, sans-serif",
    boxShadow: "0 8px 30px rgba(0, 0, 0, 0.25)"
  }),

  header: (tokens) => ({
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacing_unit || 8,
    paddingBottom: tokens.spacing_unit ? tokens.spacing_unit * 2 : 16,
    borderBottom: "1px solid rgba(148, 163, 184, 0.18)"
  }),

  title: (tokens) => ({
    fontSize: 24,
    fontWeight: 700,
    color: tokens.text_color || "#E2E8F0"
  }),

  questId: (tokens) => ({
    fontSize: 13,
    color: tokens.muted_text_color || "#94A3B8",
    fontFamily: "monospace"
  }),

  nodeList: (tokens) => ({
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacing_unit ? tokens.spacing_unit * 2 : 16
  }),

  nodeCard: (tokens, node) => {
    const base = {
      borderRadius: tokens.radius || 12,
      padding: tokens.spacing_unit ? tokens.spacing_unit * 2 : 16,
      border: `${tokens.border_width || 1}px solid rgba(148, 163, 184, 0.2)`,
      background: "rgba(15, 23, 42, 0.35)",
      transition: "all 160ms ease"
    };

    if (node.is_active) {
      return {
        ...base,
        border: `${(tokens.border_width || 1) + 1}px solid ${tokens.accent_active || "#38BDF8"}`,
        boxShadow: `0 0 18px ${(tokens.accent_active || "#38BDF8")}33`,
        background: "rgba(56, 189, 248, 0.08)"
      };
    }

    if (node.is_completed) {
      return {
        ...base,
        border: `1px solid ${tokens.accent_completed || "#22C55E"}55`,
        background: "rgba(34, 197, 94, 0.06)",
        opacity: 0.92
      };
    }

    if (node.is_locked) {
      return {
        ...base,
        opacity: 0.55,
        border: `1px dashed ${tokens.accent_locked || "#64748B"}66`
      };
    }

    return base;
  },

  nodeTopRow: (tokens) => ({
    display: "flex",
    alignItems: "center",
    gap: tokens.spacing_unit || 8,
    flexWrap: "wrap"
  }),

  nodeIndex: (tokens) => ({
    width: 28,
    height: 28,
    borderRadius: 999,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "rgba(148, 163, 184, 0.12)",
    color: tokens.muted_text_color || "#94A3B8",
    fontSize: 13,
    fontWeight: 700,
    flexShrink: 0
  }),

  nodeConcept: (tokens, node) => ({
    flex: 1,
    fontSize: 15,
    fontWeight: 600,
    color: node.is_active
      ? (tokens.accent_active || "#38BDF8")
      : (tokens.text_color || "#E2E8F0"),
    fontFamily: "monospace"
  }),

  activeBadge: (tokens) => ({
    fontSize: 11,
    fontWeight: 800,
    letterSpacing: "0.08em",
    color: "#082F49",
    background: tokens.accent_active || "#38BDF8",
    borderRadius: 999,
    padding: "4px 10px"
  }),

  completedBadge: (tokens) => ({
    fontSize: 11,
    fontWeight: 800,
    letterSpacing: "0.08em",
    color: "#052E16",
    background: tokens.accent_completed || "#22C55E",
    borderRadius: 999,
    padding: "4px 10px"
  }),

  lockedBadge: (tokens) => ({
    fontSize: 11,
    fontWeight: 800,
    letterSpacing: "0.08em",
    color: "#0F172A",
    background: tokens.accent_locked || "#64748B",
    borderRadius: 999,
    padding: "4px 10px"
  }),

  nodeMeta: (tokens) => ({
    display: "flex",
    flexDirection: "column",
    gap: 6,
    marginTop: tokens.spacing_unit || 8,
    paddingLeft: 36
  }),

  nodeId: (tokens) => ({
    fontSize: 12,
    color: tokens.muted_text_color || "#94A3B8",
    fontFamily: "monospace"
  }),

  activeHint: (tokens) => ({
    fontSize: 13,
    color: tokens.accent_active || "#38BDF8"
  }),

  lockedHint: (tokens) => ({
    fontSize: 13,
    color: tokens.muted_text_color || "#94A3B8"
  }),

  completedHint: (tokens) => ({
    fontSize: 13,
    color: tokens.accent_completed || "#22C55E"
  }),

  footer: (tokens) => ({
    display: "flex",
    flexDirection: "column",
    gap: tokens.spacing_unit || 8,
    paddingTop: tokens.spacing_unit ? tokens.spacing_unit * 2 : 16,
    borderTop: "1px solid rgba(148, 163, 184, 0.18)"
  }),

  footerLabel: (tokens) => ({
    fontSize: 13,
    fontWeight: 700,
    color: tokens.muted_text_color || "#94A3B8",
    textTransform: "uppercase",
    letterSpacing: "0.08em"
  }),

  edgeList: (tokens) => ({
    display: "flex",
    flexDirection: "column",
    gap: 8
  }),

  emptyEdge: (tokens) => ({
    fontSize: 13,
    color: tokens.muted_text_color || "#94A3B8"
  }),

  edgeItem: (tokens) => ({
    display: "flex",
    alignItems: "center",
    gap: 8,
    fontSize: 13,
    fontFamily: "monospace",
    color: tokens.text_color || "#E2E8F0"
  }),

  edgeNode: (tokens) => ({
    padding: "4px 8px",
    borderRadius: 8,
    background: "rgba(148, 163, 184, 0.1)"
  }),

  edgeArrow: (tokens) => ({
    color: tokens.accent_primary || "#3B82F6",
    fontWeight: 700
  }),

  loadingRoot: {
    padding: 24,
    borderRadius: 12,
    background: "#111827",
    color: "#94A3B8",
    fontFamily: "Inter, system-ui, sans-serif"
  },

  loadingText: {
    fontSize: 14
  },

  errorRoot: {
    padding: 24,
    borderRadius: 12,
    background: "#111827",
    color: "#F87171",
    fontFamily: "Inter, system-ui, sans-serif"
  },

  errorTitle: {
    fontWeight: 800,
    marginBottom: 8
  },

  errorMessage: {
    fontSize: 14,
    color: "#FCA5A5"
  }
};