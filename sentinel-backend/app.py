from __future__ import annotations

import os
import random
from flask import Flask, request, jsonify
from flask_cors import CORS

from model_loader import load_model, analyze_text, predict_stance_sentiment
from factcheck import get_veracity_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from harm_scorer import EnhancedHarmfulnessScorer
from simulation.core import make_social_graph, assign_user_profiles, DigitalTwinSimulator
from simulation.metrics import cascade_size, time_to_peak, compute_Rt
import numpy as np
import random
from simulator import run_simulation, run_digital_twin


def create_app() -> Flask:
    app = Flask(__name__)

    CORS(
        app,
        resources={r"/*": {"origins": os.getenv("CORS_ORIGIN", "*")}},
        supports_credentials=False,
    )

    # Load seq2seq or classifier model (legacy) once at startup
    app.config["MODEL"] = load_model(os.getenv("MODEL_NAME"))

    # M2: Harm Engine (stance + sentiment classifiers)
    stance_path = os.getenv(
        "STANCE_MODEL_PATH",
        r"C:\Users\harsh\OneDrive\Desktop\m1\stance model",
    )
    sentiment_path = os.getenv(
        "SENTIMENT_MODEL_PATH",
        r"C:\Users\harsh\OneDrive\Desktop\m1\sentiment model",
    )
    try:
        stance_tok = AutoTokenizer.from_pretrained(stance_path)
        stance_model = AutoModelForSequenceClassification.from_pretrained(stance_path)
    except Exception:
        stance_tok = None
        stance_model = None
    try:
        sentiment_tok = AutoTokenizer.from_pretrained(sentiment_path)
        sentiment_model = AutoModelForSequenceClassification.from_pretrained(sentiment_path)
    except Exception:
        sentiment_tok = None
        sentiment_model = None

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    for m in (stance_model, sentiment_model):
        if m is not None:
            m.to(device)
            m.eval()

    app.config.update(
        {
            "STANCE_TOKENIZER": stance_tok,
            "STANCE_MODEL": stance_model,
            "SENTIMENT_TOKENIZER": sentiment_tok,
            "SENTIMENT_MODEL": sentiment_model,
            "DEVICE": device,
        }
    )

    # Digital twin base graph (built once)
    try:
        base_G, base_comms = make_social_graph(
            n=int(os.getenv("DT_GRAPH_N", "800")),
            m=int(os.getenv("DT_GRAPH_M", "3")),
            community_frac=float(os.getenv("DT_COMMUNITY_FRAC", "0.2")),
            seed=int(os.getenv("DT_SEED", "123")),
        )
        base_G = assign_user_profiles(base_G, base_comms)
        app.config["DT_GRAPH"] = base_G
        app.config["DT_COMMS"] = base_comms
    except Exception:
        app.config["DT_GRAPH"] = None
        app.config["DT_COMMS"] = None

    def predict_stance(text: str) -> tuple[int, str]:
        tok: AutoTokenizer | None = app.config.get("STANCE_TOKENIZER")
        mdl: AutoModelForSequenceClassification | None = app.config.get("STANCE_MODEL")
        if not tok or not mdl:
            return -1, "unknown"
        inputs = tok(text, return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(app.config["DEVICE"]) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = mdl(**inputs)
        pred_id = int(torch.argmax(outputs.logits, dim=1).item())
        label_map = getattr(mdl.config, "id2label", {}) or {}
        return pred_id, str(label_map.get(pred_id, pred_id))

    def predict_sentiment(text: str) -> tuple[int, str]:
        tok: AutoTokenizer | None = app.config.get("SENTIMENT_TOKENIZER")
        mdl: AutoModelForSequenceClassification | None = app.config.get("SENTIMENT_MODEL")
        if not tok or not mdl:
            return -1, "unknown"
        inputs = tok(text, return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(app.config["DEVICE"]) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = mdl(**inputs)
        pred_id = int(torch.argmax(outputs.logits, dim=1).item())
        label_map = getattr(mdl.config, "id2label", {}) or {}
        return pred_id, str(label_map.get(pred_id, pred_id))

    def calculate_harm(stance_id: int, sentiment_id: int, stance_label: str, sentiment_label: str) -> float:
        # Prefer label-based logic if available, else fallback to ids
        stance_l = (stance_label or "").lower()
        sentiment_l = (sentiment_label or "").lower()
        # Example heuristic; adjust as per your training schema
        if stance_l == "support" and sentiment_l in {"positive", "pos"}:
            return 0.9
        if stance_l == "deny" and sentiment_l in {"negative", "neg"}:
            return 0.2
        if stance_l == "question":
            return 0.5
        if stance_l == "comment":
            return 0.4
        # Fallback using ids if labels are unknown (e.g., 0=support,1=deny,2=question,3=comment; 0=neg,1=neu,2=pos)
        if stance_id == 0 and sentiment_id == 2:
            return 0.9
        if stance_id == 1 and sentiment_id == 0:
            return 0.2
        if stance_id == 2:
            return 0.5
        return 0.4

    @app.get("/health")
    def health() -> tuple[dict, int]:
        return {"status": "ok"}, 200

    @app.post("/analyze")
    def analyze() -> tuple[dict, int]:
        payload = request.get_json(silent=True) or {}
        text = payload.get("text", "").strip()
        comments = payload.get("comments") or []
        if not text:
            return {"error": "Missing 'text'"}, 400

        # M2: Harm Engine via EnhancedHarmfulnessScorer (uses stance + sentiment models)
        scorer = EnhancedHarmfulnessScorer(
            sentiment_model_path=os.getenv(
                "SENTIMENT_MODEL_PATH", r"C:\Users\harsh\OneDrive\Desktop\m1\sentiment model"
            ),
            stance_model_path=os.getenv(
                "STANCE_MODEL_PATH", r"C:\Users\harsh\OneDrive\Desktop\m1\stance model"
            ),
        )
        # If no comments provided, analyze the single rumor text as a minimal thread
        thread = comments if isinstance(comments, list) and comments else [{"text": text}]
        harm_result = scorer.analyze_conversation_thread(thread, "rumor_thread")
        harm_score = float(harm_result.get("harmfulness_score", 0.0))

        # M3: Veracity via Fact Check API
        veracity = float(get_veracity_score(text))

        # M4: Threat = Harm * (1 - Veracity)
        threat = round(harm_score * (1.0 - veracity), 3)

        return jsonify(
            {
                "rumor": text,
                "harm": harm_result,
                "harm_score": round(harm_score, 3),
                "veracity_score": round(veracity, 3),
                "threat_score": threat,
            }
        ), 200

    def _extract_subgraph_posted_loc(H):
        nodes_posted = [
            n
            for n, d in H.nodes(data=True)
            if (
                d.get("posted_time") is not None
                or d.get("engaged")
                or d.get("stance") is not None
                or d.get("sentiment") is not None
            )
        ]
        nodes = []
        id_map = {}
        for i, n in enumerate(nodes_posted):
            d = H.nodes[n]
            nodes.append(
                {
                    "id": int(i),
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

    @app.post("/simulate_digital_twin")
    def simulate_digital_twin() -> tuple[dict, int]:
        data = request.get_json(silent=True) or {}
        text = data.get("text", "example rumor")
        seed_node = data.get("seed_node")
        steps = int(data.get("steps", 500))
        intervene_at = data.get("intervene_at")
        veracity_score = float(data.get("veracity_score", 0.5))

        G = app.config.get("DT_GRAPH")
        communities = app.config.get("DT_COMMS")
        if G is None:
            # build a small fallback
            G, communities = make_social_graph(n=500, m=3, community_frac=0.2, seed=123)
            G = assign_user_profiles(G, communities)

        # choose seed node
        if seed_node is None:
            # Choose a high out-degree node to ensure a visible cascade
            out_degs = dict(G.out_degree())
            sorted_nodes = sorted(out_degs.items(), key=lambda x: x[1], reverse=True)
            seed_node = sorted_nodes[0][0] if sorted_nodes else random.choice(list(G.nodes()))

        H = G.copy()
        sim = DigitalTwinSimulator(
            H,
            communities=communities,
            base_virality=float(os.getenv("DT_BASE_VIRALITY", "0.32")),
            seed=42,
        )
        sim.seed_rumor(seed_node, text, init_time=0.0, model_predictor=None)
        timeline = sim.step(
            dt=1.0,
            model_predictor=None,
            veracity_score=veracity_score,
            intervene_at=intervene_at,
            intervention_effect=0.5,
            mutation_prob=0.02,
            max_steps=steps,
        )

        sizes = cascade_size(timeline)
        peak_t = time_to_peak(timeline)
        Rt = compute_Rt(timeline)
        # Compute final harm on posted nodes' texts using your scorer
        harm_score = 0.0
        harm_result = None
        try:
            selected_nodes = [
                n
                for n, d in H.nodes(data=True)
                if (
                    d.get("posted_time") is not None
                    or d.get("engaged")
                    or d.get("stance") is not None
                    or d.get("sentiment") is not None
                )
            ]
            comments = []
            for n in selected_nodes:
                d = H.nodes[n]
                txt = d.get("text") or text  # fallback to rumor text so scorer has content
                comments.append({"text": txt, "user.handle": f"u{n}"})
            scorer = EnhancedHarmfulnessScorer(
                sentiment_model_path=os.getenv("SENTIMENT_MODEL_PATH"),
                stance_model_path=os.getenv("STANCE_MODEL_PATH"),
            )
            harm_result = scorer.analyze_conversation_thread(comments, "rumor_thread")
            harm_score = float(harm_result.get("harmfulness_score", 0.0))
        except Exception:
            harm_result = {"harmfulness_score": 0.0}
            harm_score = 0.0

        # Fallback: if harm_result is empty or error, derive harm from last timeline snapshot
        if (not harm_result) or harm_result.get("error") or (harm_score == 0.0):
            last = timeline[-1] if timeline else None
            if last:
                sent_counts = last.get("sentiment_counts", {})
                stance_counts = last.get("stance_counts", {})
                neg = float(sent_counts.get("negative", 0))
                pos = float(sent_counts.get("positive", 0))
                emo_total = max(1.0, neg + pos)
                R_c = neg / emo_total

                sup = float(stance_counts.get("support", 0))
                deny = float(stance_counts.get("deny", 0))
                ques = float(stance_counts.get("question", 0))
                stance_total = max(1.0, sup + deny + ques)
                R_r = sup / stance_total

                # Simple proxies for organization/engagement/controversy
                engagement = min(last.get("cascade_size", 0) / 50.0, 1.0)
                # entropy-like: more unique keys -> higher
                import math
                def entropy_from_counts(d):
                    total = sum(d.values()) or 1.0
                    e = 0.0
                    for v in d.values():
                        p = v / total
                        if p > 0:
                            e -= p * math.log(p + 1e-9, 2)
                    return e
                controversy = min((entropy_from_counts(sent_counts) + entropy_from_counts(stance_counts)) / 4.0, 1.0)
                organization = 0.2  # baseline
                emotional_intensity = (neg + pos) / max(1.0, sum(sent_counts.values()))
                opposition = min(
                    sup / max(1.0, sum(stance_counts.values())),
                    deny / max(1.0, sum(stance_counts.values())),
                ) * 2.0

                weights = {
                    'sentimentality': 0.25,
                    'approval': 0.25,
                    'organization': 0.20,
                    'engagement': 0.10,
                    'controversy': 0.10,
                    'emotional_intensity': 0.05,
                    'opposition': 0.05,
                }
                harm_score = (
                    weights['sentimentality'] * R_c +
                    weights['approval'] * R_r +
                    weights['organization'] * organization +
                    weights['engagement'] * engagement +
                    weights['controversy'] * controversy +
                    weights['emotional_intensity'] * emotional_intensity +
                    weights['opposition'] * opposition
                )
                harm_result = {
                    'harmfulness_score': harm_score,
                    'harmfulness_score_normalized': harm_score * 100.0,
                    'components': {
                        'rumor_sentimentality_R_c': R_c,
                        'rumor_approval_R_r': R_r,
                        'organization_score_R_o': organization,
                        'engagement_score': engagement,
                        'controversy_score': controversy,
                        'emotional_intensity_score': emotional_intensity,
                        'opposition_score': opposition,
                        'sentiment_distribution': sent_counts,
                        'stance_distribution': stance_counts,
                        'total_comments': last.get('cascade_size', 0),
                        'unique_users': last.get('cascade_size', 0),
                    },
                    'comment_count': last.get('cascade_size', 0)
                }

        threat_score = round(float(harm_score) * (1.0 - veracity_score), 3)

        return jsonify(
            {
                "rumor": text,
                "summary": {
                    "cascade_final_size": int(sizes[-1]) if sizes else 0,
                    "time_to_peak": peak_t,
                    "Rt_mean": float(np.mean(Rt)) if Rt else 0.0,
                    "timeline_len": len(timeline),
                },
                "timeline": timeline,
                "graph": _extract_subgraph_posted_loc(H),
                "harm": harm_result,
                "harm_score": round(harm_score, 3),
                "veracity_score": round(veracity_score, 3),
                "threat_score": threat_score,
            }
        ), 200

    @app.post("/simulate")
    def simulate() -> tuple[dict, int]:
        data = request.get_json(silent=True) or {}
        rumor_text = data.get("text", "")
        if not rumor_text:
            return {"error": "Missing 'text'"}, 400

        # Digital twin graph + per-step harm metrics
        twin = run_digital_twin(
            rumor_text=rumor_text,
            num_nodes=int(data.get("num_nodes", 80)),
            edge_prob=float(data.get("edge_prob", 0.03)),
            spread_prob=float(data.get("spread_prob", 0.2)),
            steps=int(data.get("steps", 10)),
        )
        # Compute global scores using final step comments
        try:
            scorer = EnhancedHarmfulnessScorer(
                sentiment_model_path=os.getenv("SENTIMENT_MODEL_PATH"),
                stance_model_path=os.getenv("STANCE_MODEL_PATH"),
            )
            final_comments = twin.get("step_comments", [])[-1] if twin.get("step_comments") else []
            harm_result = scorer.analyze_conversation_thread(final_comments, "rumor_thread")
            harm_score = float(harm_result.get("harmfulness_score", 0.0))
        except Exception:
            harm_result = {"harmfulness_score": 0.0}
            harm_score = 0.0

        veracity_score = float(get_veracity_score(rumor_text))
        threat_score = round(harm_score * (1 - veracity_score), 3)

        return jsonify(
            {
                "rumor": rumor_text,
                "graph": {"nodes": twin["nodes"], "edges": twin["edges"]},
                "timeline": twin.get("timeline", []),
                "step_metrics": twin.get("step_metrics", []),
                "harm": harm_result,
                "harm_score": round(harm_score, 3),
                "veracity_score": round(veracity_score, 3),
                "threat_score": threat_score,
            }
        ), 200

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")


def _extract_subgraph_posted(H):
    nodes_posted = [n for n, d in H.nodes(data=True) if d.get("posted_time") is not None]
    nodes = []
    id_map = {}
    for i, n in enumerate(nodes_posted):
        d = H.nodes[n]
        nodes.append(
            {
                "id": int(i),
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


