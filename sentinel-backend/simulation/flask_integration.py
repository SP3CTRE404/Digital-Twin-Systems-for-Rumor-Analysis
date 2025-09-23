from flask import Flask, request, jsonify
from simulation.core import make_social_graph, assign_user_profiles, DigitalTwinSimulator
from simulation.metrics import cascade_size, time_to_peak, compute_Rt
import numpy as np
import random

app = Flask(__name__)

# create a graph once on start - small for testing, bigger for real runs
G, communities = make_social_graph(n=1500, m=3, community_frac=0.2, seed=123)
G = assign_user_profiles(G, communities)


# placeholder model predictor: you can pass a function that calls your transformer models
def model_predictor(text, node_id):
    # For now return None so simulator uses profile-based sampling.
    # Later: call your stance/sentiment classifier here and return {"stance":..., "sentiment":...}
    return {}


@app.route("/simulate_digital_twin", methods=["POST"])
def simulate_digital_twin():
    """
    Input JSON:
    {
      "text": "rumor text",
      "seed_node": optional int,
      "steps": optional int,
      "intervene_at": optional float (time) or null,
      "veracity_score": optional float [0,1] - lower means false
    }
    """
    data = request.get_json(force=True)
    text = data.get("text", "example rumor")
    seed_node = data.get("seed_node", None)
    steps = int(data.get("steps", 1000))
    intervene_at = data.get("intervene_at", None)
    veracity_score = float(data.get("veracity_score", 0.5))

    # choose seed node (influencer or random)
    if seed_node is None:
        out_degs = dict(G.out_degree())
        sorted_nodes = sorted(out_degs.items(), key=lambda x: x[1], reverse=True)
        if random.random() < 0.2 and sorted_nodes:
            seed_node = sorted_nodes[0][0]
        else:
            seed_node = random.choice(list(G.nodes()))

    # fresh copy of graph to avoid mutating the global template
    H = G.copy()
    sim = DigitalTwinSimulator(H, communities=communities, base_virality=0.18, seed=42)
    sim.seed_rumor(seed_node, text, init_time=0.0, model_predictor=model_predictor)
    timeline = sim.step(
        dt=1.0,
        model_predictor=model_predictor,
        veracity_score=veracity_score,
        intervene_at=intervene_at,
        intervention_effect=0.5,
        mutation_prob=0.02,
        max_steps=steps,
    )

    sizes = cascade_size(timeline)
    peak_t = time_to_peak(timeline)
    Rt = compute_Rt(timeline)
    response = {
        "summary": {
            "cascade_final_size": int(sizes[-1]) if sizes else 0,
            "time_to_peak": peak_t,
            "Rt_mean": float(np.mean(Rt)) if Rt else 0.0,
            "timeline_len": len(timeline),
        },
        "timeline": timeline,
        # Provide graph: all nodes that posted and edges among them
        "graph": _extract_subgraph_posted(H),
    }
    return jsonify(response)


def _extract_subgraph_posted(H):
    nodes_posted = [n for n, d in H.nodes(data=True) if d.get("posted_time") is not None]
    nodes = []
    id_map = {}
    for i, n in enumerate(nodes_posted):
        d = H.nodes[n]
        nodes.append(
            {
                "id": int(n),
                "posted_time": float(d.get("posted_time", 0.0)),
                "stance": d.get("stance"),
                "sentiment": d.get("sentiment"),
                "influence": float(d.get("influence", 0.0)),
            }
        )
        id_map[n] = i
    edges = []
    for u, v in H.edges():
        if u in nodes_posted and v in nodes_posted:
            edges.append({"source": id_map[u], "target": id_map[v]})
    return {"nodes": nodes, "edges": edges}


if __name__ == "__main__":
    app.run(debug=True, port=5001)






