"""
Advanced Digital Twin Simulator for Rumor Analysis with Realistic Network Dynamics
"""
from __future__ import annotations

import os
import random
import warnings
from typing import Any, Dict, List, Optional, Set

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from simulation.comment_generator import generate_conversation

try:
    from harm_scorer import EnhancedHarmfulnessScorer
except Exception:
    EnhancedHarmfulnessScorer = None

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class AdvancedDigitalTwin:
    """Advanced Digital Twin class for rumor analysis with realistic network dynamics"""
    
    def __init__(
        self,
        num_nodes: int = 100,
        edge_prob: float = 0.03,
        spread_prob: float = 0.2,
        steps: int = 10
    ):
        """Initialize the digital twin simulation"""
        self.num_nodes = num_nodes
        self.edge_prob = edge_prob
        self.spread_prob = spread_prob
        self.steps = steps
        self.rng = random.Random(42)
        
        # Node attribute options
        self.user_types = ["regular", "influencer", "skeptic", "amplifier"]
        self.stances = ["support", "deny", "query", "neutral"]
        
        # Initialize components
        self._init_network()
        self._init_scorer()
        self._setup_visualization()
    
    def _init_network(self):
        """Initialize network with rich node attributes"""
        self.graph = nx.erdos_renyi_graph(self.num_nodes, self.edge_prob, seed=42)
        
        # Initialize nodes with rich attributes
        for n in self.graph.nodes:
            self.graph.nodes[n].update({
                "user_type": self.rng.choice(self.user_types),
                "stance_bias": self.rng.choice(self.stances),
                "influence_score": self.rng.uniform(0.1, 1.0),
                "activity_level": self.rng.uniform(0.2, 0.8)
            })
    
    def _init_scorer(self):
        """Initialize the harmfulness scorer"""
        self.scorer = None
        if EnhancedHarmfulnessScorer is not None:
            try:
                self.scorer = EnhancedHarmfulnessScorer()
                print("✅ Initialized harm scorer successfully")
            except Exception as e:
                print(f"❌ Failed to initialize harm scorer: {e}")
    
    def _setup_visualization(self):
        """Setup visualization directory"""
        self.vis_dir = "results/simulation_vis"
        os.makedirs(self.vis_dir, exist_ok=True)
    
    def _generate_step_visualization(self, step: int, active: Set[int]):
        """Generate network visualization for current step"""
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(self.graph)
        
        # Draw inactive nodes
        nx.draw_networkx_nodes(self.graph, pos,
                             nodelist=[n for n in self.graph.nodes() if n not in active],
                             node_color='lightgray',
                             node_size=100)
        
        # Draw active nodes colored by stance
        for stance in self.stances:
            nodelist = [n for n in active if self.graph.nodes[n]['stance_bias'] == stance]
            if nodelist:
                nx.draw_networkx_nodes(self.graph, pos,
                                     nodelist=nodelist,
                                     node_color={'support': 'green',
                                               'deny': 'red',
                                               'query': 'orange',
                                               'neutral': 'blue'}[stance],
                                     node_size=200)
        
        nx.draw_networkx_edges(self.graph, pos, alpha=0.2)
        plt.title(f"Step {step}: {len(active)} Active Nodes")
        plt.savefig(os.path.join(self.vis_dir, f"step_{step}.png"))
        plt.close()
    
    def _generate_final_analysis(self, per_step_metrics: List[Dict]):
        """Generate final analysis visualization"""
        plt.figure(figsize=(15, 5))
        
        # Plot harm score evolution
        plt.subplot(131)
        harm_scores = [m.get('harm_score', 0) for m in per_step_metrics]
        plt.plot(harm_scores, marker='o')
        plt.title('Harm Score Evolution')
        plt.xlabel('Step')
        plt.ylabel('Harm Score')
        
        # Plot network metrics
        plt.subplot(132)
        coverage = [m['coverage'] for m in per_step_metrics]
        density = [m['density'] for m in per_step_metrics]
        plt.plot(coverage, label='Coverage', marker='s')
        plt.plot(density, label='Density', marker='o')
        plt.title('Network Metrics')
        plt.xlabel('Step')
        plt.ylabel('Score')
        plt.legend()
        
        # Plot engagement metrics
        plt.subplot(133)
        sentiment_scores = [m.get('sentiment_score', 0) for m in per_step_metrics]
        stance_scores = [m.get('stance_score', 0) for m in per_step_metrics]
        plt.plot(sentiment_scores, label='Sentiment', marker='o')
        plt.plot(stance_scores, label='Stance', marker='s')
        plt.title('Engagement Metrics')
        plt.xlabel('Step')
        plt.ylabel('Score')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.vis_dir, 'final_analysis.png'))
        plt.close()
    
    def run_simulation(self, rumor_text: str) -> Dict[str, Any]:
        """Run the digital twin simulation"""
        active: Set[int] = {0}  # Start with node 0
        timeline_nodes: List[List[int]] = [sorted(active)]
        comments_over_time: List[List[Dict[str, Any]]] = []
        per_step_metrics: List[Dict[str, Any]] = []
        
        for step in range(self.steps):
            # Generate comments
            active_nodes_attrs = [self.graph.nodes[n] for n in active]
            step_comments = generate_conversation(active_nodes_attrs, rumor_text)
            comments_over_time.append(step_comments)
            
            # Calculate metrics
            harm_metrics = self._calculate_harm_metrics(rumor_text, step_comments)
            network_metrics = self._calculate_network_metrics(active)
            per_step_metrics.append({**harm_metrics, **network_metrics})
            
            # Generate visualization
            if step % 2 == 0:
                self._generate_step_visualization(step, active)
            
            # Update network state
            next_active = self._propagate_influence(active)
            if next_active == active:
                break
            active = next_active
            timeline_nodes.append(sorted(active))
        
        # Generate final analysis
        self._generate_final_analysis(per_step_metrics)
        
        coverage = per_step_metrics[-1]['coverage'] if per_step_metrics else 0
        
        return {
            "nodes": [{
                "id": int(n),
                "type": self.graph.nodes[n]["user_type"],
                "stance": self.graph.nodes[n]["stance_bias"],
                "influence": self.graph.nodes[n]["influence_score"],
                "activity": self.graph.nodes[n]["activity_level"]
            } for n in self.graph.nodes()],
            "edges": [{"source": int(u), "target": int(v)} for u, v in self.graph.edges()],
            "timeline": timeline_nodes,
            "step_comments": comments_over_time,
            "step_metrics": per_step_metrics,
            "final_coverage": coverage,
            "visualizations": {
                "steps": [f"{self.vis_dir}/step_{i}.png" for i in range(0, self.steps, 2)],
                "final": f"{self.vis_dir}/final_analysis.png"
            }
        }
    
    def _calculate_harm_metrics(self, rumor_text: str, comments: List[Dict]) -> Dict[str, float]:
        """Calculate harm metrics using the scorer"""
        if not self.scorer:
            return {
                "harm_score": 0.0,
                "sentiment_score": 0.0,
                "stance_score": 0.0,
                "organization_score": 0.0
            }
        
        try:
            comments_df = pd.DataFrame(comments)
            harm_analysis = self.scorer.calculate_harmfulness_score(rumor_text, comments_df)
            return {
                "harm_score": round(harm_analysis.get("harmfulness_score", 0.0), 4),
                "sentiment_score": round(harm_analysis.get("sentiment_score", 0.0), 4),
                "stance_score": round(harm_analysis.get("stance_score", 0.0), 4),
                "organization_score": round(harm_analysis.get("organization_score", 0.0), 4)
            }
        except Exception as e:
            print(f"Error calculating harm metrics: {e}")
            return {
                "harm_score": 0.0,
                "sentiment_score": 0.0,
                "stance_score": 0.0,
                "organization_score": 0.0
            }
    
    def _calculate_network_metrics(self, active: Set[int]) -> Dict[str, float]:
        """Calculate network metrics for the current state"""
        return {
            "active_count": len(active),
            "coverage": round(len(active) / self.graph.number_of_nodes(), 4),
            "density": round(nx.density(self.graph.subgraph(active)), 4) if len(active) > 1 else 0.0,
            "clustering": round(nx.average_clustering(self.graph.subgraph(active)), 4) if len(active) > 1 else 0.0
        }
    
    def _propagate_influence(self, active: Set[int]) -> Set[int]:
        """Propagate influence through the network"""
        next_active = set(active)
        for n in list(active):
            node_influence = self.graph.nodes[n]['influence_score']
            for m in self.graph.neighbors(n):
                if m in next_active:
                    continue
                # Adjust spread probability based on influence and activity
                adjusted_prob = self.spread_prob * node_influence * self.graph.nodes[m]['activity_level']
                if self.rng.random() < adjusted_prob:
                    next_active.add(m)
        return next_active

def run_digital_twin(
    rumor_text: str,
    num_nodes: int = 100,
    edge_prob: float = 0.03,
    spread_prob: float = 0.2,
    steps: int = 10
) -> Dict[str, Any]:
    """Run a digital twin simulation with the given parameters"""
    simulator = AdvancedDigitalTwin(
        num_nodes=num_nodes,
        edge_prob=edge_prob,
        spread_prob=spread_prob,
        steps=steps
    )
    return simulator.run_simulation(rumor_text)