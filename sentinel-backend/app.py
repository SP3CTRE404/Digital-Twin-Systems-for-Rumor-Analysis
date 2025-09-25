from __future__ import annotations

import os
import random
from flask import Flask, request, jsonify
from flask_cors import CORS

from model_loader import load_model, analyze_text, predict_stance_sentiment
from factcheck import analyze_thread_veracity
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from harm_scorer import EnhancedHarmfulnessScorer
from threat_scorer import ThreatScorer
from simulation.core import make_social_graph, assign_user_profiles, DigitalTwinSimulator
from simulation.metrics import cascade_size, time_to_peak, compute_Rt
from simulation.comment_generator import AdvancedSimulator
from threat_route import threat_bp
import numpy as np
import pandas as pd
import random


def create_app() -> Flask:
    app = Flask(__name__)

    # Configure CORS
    CORS(
        app,
        resources={r"/*": {"origins": os.getenv("CORS_ORIGIN", "*")}},
        supports_credentials=False,
    )
    
    # Register blueprints
    app.register_blueprint(threat_bp)

    # Initialize components
    try:
        # 1. Comment Generator
        app.config["COMMENT_GENERATOR"] = AdvancedSimulator()
        print("✅ Comment generator initialized successfully")
        
        # 2. Model paths
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        stance_path = os.getenv(
            "STANCE_MODEL_PATH",
            os.path.join(base_dir, "models", "stance_model_3050"),
        )
        sentiment_path = os.getenv(
            "SENTIMENT_MODEL_PATH",
            os.path.join(base_dir, "models", "sentiment_model_3050"),
        )
        
        # 3. Harm Scorer
        harm_scorer = EnhancedHarmfulnessScorer(
            sentiment_model_path=sentiment_path,
            stance_model_path=stance_path
        )
        app.config["HARM_SCORER"] = harm_scorer
        print("✅ Harm scorer initialized successfully")
        
        # 4. Threat Scorer
        threat_scorer = ThreatScorer(harm_scorer=harm_scorer)
        app.config["THREAT_SCORER"] = threat_scorer
        print("✅ Threat scorer initialized successfully")
        
    except Exception as e:
        print(f"❌ Error initializing components: {e}")
        app.config["COMMENT_GENERATOR"] = None
        app.config["HARM_SCORER"] = None
        app.config["THREAT_SCORER"] = None
    
    try:
        app.config["HARM_SCORER"] = EnhancedHarmfulnessScorer(
            sentiment_model_path=sentiment_path,
            stance_model_path=stance_path,
        )
        print("✅ Harm scorer initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize harm scorer: {e}")
        app.config["HARM_SCORER"] = None

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
        print("✅ Digital twin graph initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize digital twin graph: {e}")
        app.config["DT_GRAPH"] = None
        app.config["DT_COMMS"] = None

    @app.get("/health")
    def health() -> tuple[dict, int]:
        return {"status": "ok"}, 200

    @app.post("/analyze")
    def analyze() -> tuple[dict, int]:
        """Analyze a rumor with optional comments for harmfulness"""
        try:
            payload = request.get_json()
            if not payload:
                return {"error": "Invalid JSON payload"}, 400
                
            text = payload.get("rumor", "").strip()
            if not text:
                return {"error": "Missing or empty 'text' field"}, 400

            comments = payload.get("comments") or []
            if not isinstance(comments, list):
                return {"error": "Comments must be an array"}, 400

            scorer = app.config.get("HARM_SCORER")
            if not scorer:
                return {"error": "Harm scorer not available"}, 500

            # If no comments provided, generate them using AI
            if not comments:
                comment_gen = app.config.get("COMMENT_GENERATOR")
                if comment_gen:
                    print("Generating realistic comments using AI...")
                    try:
                        ai_comments = comment_gen.generate_thread(
                            rumor_text=text,
                            num_comments=12,
                            topic_context="social media rumor discussion"
                        )
                        # Convert to format expected by harm scorer
                        comments = []
                        for comment in ai_comments:
                            comments.append({
                                "text": comment.get("comment_text", ""),
                                "user.handle": comment.get("username", "anonymous"),
                                "stance": comment.get("stance", "comment"),
                                "user_type": comment.get("user_type", "regular")
                            })
                        print(f"Generated {len(comments)} AI comments")
                    except Exception as e:
                        print(f"AI comment generation failed: {e}")
                        # Fallback to simple synthetic comments
                        comments = [{"text": text, "user.handle": "seed_user"}]
                else:
                    # Fallback to analyzing just the rumor text
                    comments = [{"text": text, "user.handle": "seed_user"}]

            # Analyze harmfulness
            try:
                harm_result = scorer.analyze_conversation_thread(comments, "rumor_thread")
                harm_score = float(harm_result.get("harmfulness_score", 0.0))
            except Exception as e:
                return {"error": f"Failed to analyze harmfulness: {str(e)}"}, 500

            # Get veracity score
            try:
                veracity_result = analyze_thread_veracity(text, [], api_key=os.getenv("GOOGLE_FACTCHECK_API_KEY"))
                veracity = veracity_result['rumor_veracity']['score']
            except Exception as e:
                print(f"Veracity check failed: {e}")
                veracity = 0.5  # Default neutral veracity

            # Calculate threat score: Harm * (1 - Veracity)
            threat = round(harm_score * (1.0 - veracity), 3)

            return jsonify({
                "rumor": text,
                "generated_comments": len(comments) if comments else 0,
                "comments_sample": comments[:3] if len(comments) > 3 else comments,
                "harm": harm_result,
                "harm_score": round(harm_score, 3),
                "veracity_score": round(veracity, 3),
                "threat_score": threat,
            }), 200
            
        except Exception as e:
            return {"error": f"Internal server error: {str(e)}"}, 500

    @app.post("/simulate_digital_twin")
    def simulate_digital_twin() -> tuple[dict, int]:
        """Run enhanced digital twin simulation with realistic comments"""
        try:
            data = request.get_json(silent=True) or {}
            text = data.get("text", "example rumor")
            seed_node = data.get("seed_node")
            steps = int(data.get("steps", 300))
            intervene_at = data.get("intervene_at")
            veracity_score = float(data.get("veracity_score", 0.5))

            # Get components
            G = app.config.get("DT_GRAPH")
            communities = app.config.get("DT_COMMS")
            scorer = app.config.get("HARM_SCORER")
            comment_gen = app.config.get("COMMENT_GENERATOR")

            if G is None:
                # Build fallback graph
                G, communities = make_social_graph(n=500, m=3, community_frac=0.2, seed=123)
                G = assign_user_profiles(G, communities)

            # Choose seed node
            if seed_node is None:
                out_degs = dict(G.out_degree())
                sorted_nodes = sorted(out_degs.items(), key=lambda x: x[1], reverse=True)
                seed_node = sorted_nodes[0][0] if sorted_nodes else random.choice(list(G.nodes()))

            seed = data.get("seed", random.randint(0, 100000))

            # Create simulation copy
            H = G.copy()
            sim = DigitalTwinSimulator(
                H,
                communities=communities,
                base_virality=float(os.getenv("DT_BASE_VIRALITY", "0.25")),
                seed=seed,
            )

            # Seed the rumor
            sim.seed_rumor(seed_node, text, init_time=0.0, model_predictor=None)
            
            # Run simulation
            timeline = sim.step(
                dt=1.0,
                model_predictor=None,
                veracity_score=veracity_score,
                intervene_at=intervene_at,
                intervention_effect=0.5,
                mutation_prob=0.02,
                max_steps=steps,
            )

            # Calculate metrics
            sizes = cascade_size(timeline)
            peak_t = time_to_peak(timeline)
            Rt = compute_Rt(timeline)

            # Generate realistic comments for final state if AI available
            final_comments = []
            harm_score = 0.0
            harm_result = {"harmfulness_score": 0.0}

            # Get nodes that participated in spreading
            active_nodes = [
                n for n, d in H.nodes(data=True)
                if d.get("posted_time") is not None
            ]

            if comment_gen and len(active_nodes) > 0:
                print(f"Generating comments for {len(active_nodes)} active nodes...")
                try:
                    # Generate diverse comment thread
                    ai_comments = comment_gen.generate_thread(
                        rumor_text=text,
                        num_comments=min(len(active_nodes), 20),
                        topic_context="viral social media rumor"
                    )
                    
                    # Convert and assign to nodes
                    for i, comment in enumerate(ai_comments):
                        if i < len(active_nodes):
                            node_id = active_nodes[i]
                            comment_data = {
                                "text": comment.get("comment_text", text),
                                "user.handle": f"user_{node_id}",
                                "stance": comment.get("stance", "comment"),
                                "user_type": comment.get("user_type", "regular")
                            }
                            final_comments.append(comment_data)
                            
                            # Update node with realistic data
                            H.nodes[node_id]["text"] = comment_data["text"]
                            H.nodes[node_id]["stance"] = comment_data["stance"]

                    print(f"Generated {len(final_comments)} realistic comments")
                    
                except Exception as e:
                    print(f"Comment generation failed: {e}")

            # If no AI comments, create basic ones from active nodes
            if not final_comments and len(active_nodes) > 0:
                for node_id in active_nodes:
                    node_data = H.nodes[node_id]
                    final_comments.append({
                        "text": node_data.get("text", text),
                        "user.handle": f"user_{node_id}",
                        "stance": node_data.get("stance", "comment"),
                    })

            # Calculate harm score using generated comments
            if scorer and final_comments:
                try:
                    harm_result = scorer.analyze_conversation_thread(final_comments, "rumor_thread")
                    harm_score = float(harm_result.get("harmfulness_score", 0.0))
                except Exception as e:
                    print(f"Harm analysis failed: {e}")
                    harm_score = 0.0

            # Fallback harm calculation if scorer failed
            if harm_score == 0.0 and timeline:
                harm_score = _calculate_fallback_harm(timeline[-1])
                harm_result = {
                    'harmfulness_score': harm_score,
                    'harmfulness_score_normalized': harm_score * 100.0,
                    'components': {
                        'calculated_from': 'timeline_fallback',
                        'cascade_size': timeline[-1].get('cascade_size', 0)
                    }
                }

            # Calculate threat score
            threat_score = round(float(harm_score) * (1.0 - veracity_score), 3)

            return jsonify({
                "rumor": text,
                "summary": {
                    "cascade_final_size": int(sizes[-1]) if sizes else 0,
                    "time_to_peak": peak_t,
                    "Rt_mean": float(np.mean(Rt)) if Rt else 0.0,
                    "timeline_len": len(timeline),
                    "active_nodes": len(active_nodes),
                    "generated_comments": len(final_comments)
                },
                "timeline": timeline,
                "graph": _extract_subgraph_posted(H),
                "comments_sample": final_comments[:5] if len(final_comments) > 5 else final_comments,
                "harm": harm_result,
                "harm_score": round(harm_score, 3),
                "veracity_score": round(veracity_score, 3),
                "threat_score": threat_score,
            }), 200

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"Simulation failed: {str(e)}"}, 500

    def _calculate_fallback_harm(last_snapshot):
        """Calculate basic harm score from timeline data"""
        try:
            sent_counts = last_snapshot.get("sentiment_counts", {})
            stance_counts = last_snapshot.get("stance_counts", {})
            
            # Basic R_c calculation
            neg = float(sent_counts.get("negative", 0))
            pos = float(sent_counts.get("positive", 0))
            emo_total = max(1.0, neg + pos)
            R_c = neg / emo_total

            # Basic R_r calculation  
            sup = float(stance_counts.get("support", 0))
            deny = float(stance_counts.get("deny", 0))
            ques = float(stance_counts.get("question", 0))
            stance_total = max(1.0, sup + deny + ques)
            R_r = sup / stance_total

            # Simple engagement score
            cascade_size = last_snapshot.get("cascade_size", 0)
            engagement = min(cascade_size / 50.0, 1.0)

            # Weighted combination
            harm_score = (0.3 * R_c + 0.3 * R_r + 0.4 * engagement)
            return max(0.0, min(1.0, harm_score))
            
        except Exception:
            return 0.0

    def _extract_subgraph_posted(H):
        """Extract subgraph of nodes that posted"""
        nodes_posted = [
            n for n, d in H.nodes(data=True)
            if (d.get("posted_time") is not None or d.get("engaged"))
        ]
        
        nodes = []
        id_map = {}
        for i, n in enumerate(nodes_posted):
            d = H.nodes[n]
            nodes.append({
                "id": int(i),
                "original_id": int(n),
                "posted_time": float(d.get("posted_time", 0.0)),
                "stance": d.get("stance", "unknown"),
                "sentiment": d.get("sentiment", "neutral"),
                "influence": float(d.get("influence", 0.0)),
                "text_preview": d.get("text", "")[:50] + "..." if d.get("text", "") else ""
            })
            id_map[n] = i
        
        edges = []
        for u, v in H.edges():
            if u in nodes_posted and v in nodes_posted:
                edges.append({"source": id_map[u], "target": id_map[v]})
                
        return {"nodes": nodes, "edges": edges}

    @app.post("/simulate")  
    def simulate() -> tuple[dict, int]:
        """Simple simulation endpoint for backward compatibility"""
        data = request.get_json(silent=True) or {}
        rumor_text = data.get("text", "")
        if not rumor_text:
            return {"error": "Missing 'text'"}, 400

        # Use digital twin simulation
        return simulate_digital_twin()

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")