from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import random
import networkx as nx
import os
try:
    from harm_scorer import EnhancedHarmfulnessScorer
except Exception:
    EnhancedHarmfulnessScorer = None


def _ensure_graph(nodes: Optional[Iterable[Any]], edges: Optional[Iterable[Tuple[Any, Any]]]) -> nx.Graph:
    graph = nx.Graph()
    if nodes:
        graph.add_nodes_from(nodes)
    if edges:
        graph.add_edges_from(edges)
    # If empty, create a small default graph
    if graph.number_of_nodes() == 0:
        graph.add_nodes_from(range(10))
        for i in range(9):
            graph.add_edge(i, i + 1)
    return graph


def run_simulation(
    nodes: Optional[Iterable[Any]] = None,
    edges: Optional[Iterable[Tuple[Any, Any]]] = None,
    seed_nodes: Optional[Iterable[Any]] = None,
    spread_prob: float = 0.2,
    steps: int = 10,
) -> Dict[str, Any]:
    """Simple contagion-style spread simulation on an undirected graph.

    Returns timeline of active nodes per step and summary metrics.
    """
    rng = random.Random(42)
    graph = _ensure_graph(nodes, edges)

    active: Set[Any] = set(seed_nodes or [])
    if not active:
        # Default to node 0 as the seed if available
        if graph.number_of_nodes() > 0:
            active = {list(graph.nodes())[0]}

    timeline: List[List[Any]] = [sorted(active)]

    for _ in range(max(0, steps)):
        newly_active: Set[Any] = set(active)
        for node in list(active):
            for neighbor in graph.neighbors(node):
                if neighbor in active:
                    continue
                if rng.random() < spread_prob:
                    newly_active.add(neighbor)
        if newly_active == active:
            # Converged
            break
        active = newly_active
        timeline.append(sorted(active))

    coverage = len(active) / max(1, graph.number_of_nodes())
    return {
        "nodes": list(graph.nodes()),
        "edges": [[u, v] for u, v in graph.edges()],
        "timeline": timeline,
        "final_active": sorted(active),
        "metrics": {
            "coverage": round(coverage, 3),
            "steps": len(timeline) - 1,
        },
    }


def run_digital_twin(
    rumor_text: str,
    num_nodes: int = 100,
    edge_prob: float = 0.03,
    spread_prob: float = 0.2,
    steps: int = 10,
) -> Dict[str, Any]:
    """Digital twin simulation of rumor spread with per-step harm/threat.

    Builds a random graph, seeds node 0, propagates with probability.
    At each step, constructs a synthetic comments array from active nodes
    and evaluates harm using EnhancedHarmfulnessScorer if available.
    Veracity is evaluated once per rumor by the caller (app.py) and injected later
    or considered constant here as 0.5 if not provided.
    """
    rng = random.Random(42)
    g = nx.erdos_renyi_graph(num_nodes, edge_prob, seed=42)
    # Node biases: support/deny prior
    for n in g.nodes:
        g.nodes[n]["bias"] = rng.choice(["support", "deny", "comment"])  # coarse priors

    active: Set[int] = {0}
    timeline_nodes: List[List[int]] = [sorted(active)]

    comments_over_time: List[List[Dict[str, Any]]] = []
    # Initialize scorer if available
    scorer = None
    if EnhancedHarmfulnessScorer is not None:
        try:
            scorer = EnhancedHarmfulnessScorer(
                sentiment_model_path=os.getenv("SENTIMENT_MODEL_PATH"),
                stance_model_path=os.getenv("STANCE_MODEL_PATH"),
            )
        except Exception:
            scorer = None

    per_step_metrics: List[Dict[str, Any]] = []

    for _ in range(max(0, steps)):
        # generate comments for active nodes
        step_comments: List[Dict[str, Any]] = []
        for n in active:
            stance_hint = g.nodes[n]["bias"]
            text = f"[{stance_hint}] {rumor_text}"
            step_comments.append({"text": text, "user.handle": f"u{n}"})
        comments_over_time.append(step_comments)

        harm_score = 0.0
        if scorer is not None:
            harm_res = scorer.analyze_conversation_thread(step_comments, "rumor_thread")
            harm_score = float(harm_res.get("harmfulness_score", 0.0))
        per_step_metrics.append({"harm": round(harm_score, 4), "active_count": len(active)})

        # propagate
        next_active: Set[int] = set(active)
        for n in list(active):
            for m in g.neighbors(n):
                if m in next_active:
                    continue
                if rng.random() < spread_prob:
                    next_active.add(m)
        if next_active == active:
            break
        active = next_active
        timeline_nodes.append(sorted(active))

    return {
        "nodes": [{"id": int(n), "stance": g.nodes[n]["bias"]} for n in g.nodes()],
        "edges": [{"source": int(u), "target": int(v)} for u, v in g.edges()],
        "timeline": timeline_nodes,
        "step_comments": comments_over_time,
        "step_metrics": per_step_metrics,
    }


