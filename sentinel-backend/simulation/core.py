import random
import math
import time
import json
import numpy as np
import networkx as nx
from collections import defaultdict, deque
from copy import deepcopy

# -------------------------
# Utilities
# -------------------------
def sigmoid(x): return 1.0/(1.0+math.exp(-x))

# -------------------------
# Graph builder
# -------------------------
def make_social_graph(n=3000, m=3, community_frac=0.2, seed=42):
    """
    Build a realistic social graph:
    - base: Barabasi-Albert for power-law degree
    - then plant communities by rewiring some nodes to be more connected within communities
    Returns NetworkX DiGraph (directed follower graph).
    """
    random.seed(seed)
    np.random.seed(seed)

    # build undirected BA graph
    G = nx.barabasi_albert_graph(n, m, seed=seed)
    # convert to directed follower graph: for each undirected edge, pick direction with probability 0.5
    D = nx.DiGraph()
    D.add_nodes_from(G.nodes())
    for u, v in G.edges():
        if random.random() < 0.5:
            D.add_edge(u, v)
        else:
            D.add_edge(v, u)

    # add community structure: partition nodes into communities and rewire some edges to intra-community
    num_comms = max(2, int(n * community_frac / 50))
    nodes = list(D.nodes())
    random.shuffle(nodes)
    comm_size = n // num_comms
    communities = [nodes[i*comm_size:(i+1)*comm_size] for i in range(num_comms)]
    for i, comm in enumerate(communities):
        # add a few dense intra-community edges
        for _ in range(int(len(comm) * 0.2)):
            a, b = random.sample(comm, 2)
            D.add_edge(a, b)
    return D, communities

# -------------------------
# Node profile assignment
# -------------------------
def assign_user_profiles(G, communities=None,
                         base_biases=None,
                         influencer_fraction=0.01,
                         activity_mu=0.2):
    """
    Assign per-node attributes:
      - bias: dict of probabilities for support/deny/question/comment
      - susceptibility: how likely to reshare given exposure
      - influence: proportional to out_degree (how many followers)
      - activity_rate: baseline posting probability (controls timeliness)
    """
    if base_biases is None:
        base_biases = {
            "support": 0.25,
            "deny": 0.25,
            "question": 0.2,
            "comment": 0.3
        }
    n = G.number_of_nodes()
    nodes = list(G.nodes())
    out_degs = dict(G.out_degree())
    max_out = max(out_degs.values()) if out_degs else 1
    influencers = set(random.sample(nodes, max(1, int(n * influencer_fraction))))
    for v in nodes:
        # community-based bias shift
        comm_boost = 0.0
        if communities:
            # small boost if in particular community (make communities slightly polarized)
            for i, comm in enumerate(communities):
                if v in comm:
                    comm_boost = (i % 3 - 1) * 0.02  # small signed bias to alternate communities
                    break

        # sample bias around base using Dirichlet noise
        alpha = np.array([base_biases[k] * 20 for k in ["support","deny","question","comment"]]) + 1.0
        sampled = np.random.dirichlet(alpha)
        bias = dict(zip(["support","deny","question","comment"], sampled))
        # small deterministic community tilt
        bias["support"] = max(0, bias["support"] + comm_boost)
        # normalize
        s = sum(bias.values()) or 1.0
        bias = {k: v/s for k, v in bias.items()}

        susceptibility = float(np.clip(np.random.beta(2,5)*1.2, 0.05, 0.95))
        activity = max(0.01, np.random.exponential(scale=activity_mu))
        influence = (out_degs.get(v,0) / max_out) * (2.0 if v in influencers else 1.0)

        G.nodes[v]["bias"] = bias
        G.nodes[v]["susceptibility"] = susceptibility
        G.nodes[v]["activity"] = activity
        G.nodes[v]["influence"] = influence
        G.nodes[v]["is_influencer"] = (v in influencers)
        G.nodes[v]["engaged"] = False  # whether saw/engaged
        G.nodes[v]["posted_time"] = None
        G.nodes[v]["stance"] = None
        G.nodes[v]["sentiment"] = None
        G.nodes[v]["text"] = None

    return G

# -------------------------
# Sampling stance/sentiment
# -------------------------
def sample_reaction_from_bias(node_attr, model_probs=None, noise=0.05):
    """
    Given a node attribute dict (with bias), optionally override with model_probs (dict of p for labels)
    Return stance label and sentiment label.
    sentiment logic: correlate with stance (support->more positive, deny->more negative)
    """
    if model_probs:
        # model_probs e.g., {"support":0.6,...}
        probs = np.array([model_probs.get(k, 1e-6) for k in ["support","deny","question","comment"]], dtype=float)
        probs = probs / probs.sum()
    else:
        base = np.array([node_attr["bias"][k] for k in ["support","deny","question","comment"]])
        # add small sampling noise
        base = base + np.random.normal(0, noise, size=base.shape)
        base = np.clip(base, 1e-6, None)
        probs = base / base.sum()

    stance = np.random.choice(["support","deny","question","comment"], p=probs)

    # sentiment: map stance -> sentiment distribution
    if stance == "support":
        sentiment = np.random.choice(["positive","neutral","negative"], p=[0.6,0.25,0.15])
    elif stance == "deny":
        sentiment = np.random.choice(["negative","neutral","positive"], p=[0.6,0.3,0.1])
    elif stance == "question":
        sentiment = np.random.choice(["neutral","negative","positive"], p=[0.7,0.2,0.1])
    else:
        sentiment = np.random.choice(["neutral","negative","positive"], p=[0.6,0.25,0.15])

    return stance, sentiment

# -------------------------
# Propagation probability function
# -------------------------
def share_probability(u_attr, v_attr, base_virality=0.2, harm_factor=0.4, veracity_factor=0.6, homophily_weight=0.5, time_decay=0.5, exposure_count=1):
    """
    Compute p(u->v) for a single exposure event.
    Features considered:
      - base_virality: global virality scalar
      - u_attr['influence']: influencer boosts
      - v_attr['susceptibility']: node-specific willingness to reshare
      - homophily: similarity between u and v biases
      - harm_factor & veracity_factor are knobs you will tune
      - exposure_count: fatigue reduces chance on repeated exposures
    Returns probability in [0,1]
    """
    inf = u_attr.get("influence", 0.1)
    sus = v_attr.get("susceptibility", 0.2)
    # simple homophily: dot product of bias vectors
    b_u = np.array([u_attr["bias"][k] for k in ["support","deny","question","comment"]])
    b_v = np.array([v_attr["bias"][k] for k in ["support","deny","question","comment"]])
    hom = float(np.dot(b_u, b_v) / (np.linalg.norm(b_u)*np.linalg.norm(b_v) + 1e-9))

    # recency/time decay factor (handled outside by delay) but included as scalar
    p = base_virality * (0.5 + inf) * sus * (0.3 + homophily_weight*hom)

    # exposure fatigue: each repeat exposure multiplies by (1 - 0.2*exposures)
    p = p * (1.0 / (1.0 + 0.2*(exposure_count-1)))
    p = float(np.clip(p, 0.0, 0.99))
    return p

# -------------------------
# Event-driven simulation engine
# -------------------------
class DigitalTwinSimulator:
    def __init__(self, G, communities=None, base_virality=0.2, seed=None):
        self.G = G.copy()
        self.communities = communities
        self.base_virality = base_virality
        self.time = 0.0
        self.events = []  # list of (time, 'post', node, from_node)
        self.exposures = defaultdict(lambda: 0)  # counts exposures per node
        self.timeline = []  # list of snapshots (time, stats)
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def seed_rumor(self, seed_node, rumor_text, init_time=0.0, model_predictor=None):
        """
        Seed the rumor at seed_node at init_time.
        model_predictor: function(text, node_id) -> (stance_probs, sentiment_probs) if you want to call your classifier per node.
        """
        self.time = init_time
        self.events = [(init_time, 'post', seed_node, None, rumor_text)]
        # mark posted immediate
        self.G.nodes[seed_node]["posted_time"] = init_time
        self.G.nodes[seed_node]["engaged"] = True
        self.G.nodes[seed_node]["text"] = rumor_text

        # sample stance/sentiment for seed from model if available else bias
        if model_predictor:
            predicted = model_predictor(rumor_text, seed_node)
            stance, sentiment = predicted.get("stance"), predicted.get("sentiment")
            if not stance:
                stance, sentiment = sample_reaction_from_bias(self.G.nodes[seed_node])
        else:
            stance, sentiment = sample_reaction_from_bias(self.G.nodes[seed_node])
        self.G.nodes[seed_node]["stance"] = stance
        self.G.nodes[seed_node]["sentiment"] = sentiment

    def step(self, dt=1.0, model_predictor=None, veracity_score=0.5, intervene_at=None, intervention_effect=0.4, mutation_prob=0.02, max_steps=1000):
        """
        Run the simulation until events exhausted or max_steps reached.
        - dt is base unit (used to sample delays)
        - model_predictor: optional function for per-node model-guided reaction
        - veracity_score: (0..1) from fact-check; lower veracity -> increases spread risk in our design (we will map later)
        - intervene_at: time to inject fact-check/visibility reduction
        - intervention_effect: multiplier that reduces share_probability after intervention
        - mutation_prob: probability when a node posts that the rumor text mutates slightly
        """
        # events is a priority list: (time, 'post', node, from_node, text)
        self.events = sorted(self.events, key=lambda x: x[0])
        steps = 0
        while self.events and steps < max_steps:
            t, typ, u, from_node, text = self.events.pop(0)
            self.time = t
            steps += 1

            # Node u has posted at time t (maybe already marked)
            if self.G.nodes[u].get("posted_time") is None:
                self.G.nodes[u]["posted_time"] = t
            self.G.nodes[u]["engaged"] = True
            self.G.nodes[u]["text"] = text

            # choose neighbors (followers) who see it
            followers = list(self.G.predecessors(u))  # followers -> they see content from u
            for v in followers:
                # compute exposure count
                self.exposures[v] += 1
                # skip if already posted (we only allow one post per node in this simple model)
                if self.G.nodes[v].get("posted_time") is not None:
                    continue

                # get attributes
                u_attr = self.G.nodes[u]
                v_attr = self.G.nodes[v]

                # compute p_share
                # optionally decrease p if veracity high (truth reduces viral spread of false rumors) - mapping below
                # map veracity score to a multiplier: high veracity => reduce false rumor spread? we invert expectation: if rumor is false (low veracity), it's more viral
                veracity_multiplier = 1.0 + (1.0 - veracity_score) * 0.6
                base_p = share_probability(u_attr, v_attr, base_virality=self.base_virality)
                p = base_p * veracity_multiplier
                # if intervention already applied (time >= intervene_at)
                if intervene_at is not None and self.time >= intervene_at:
                    p *= max(0.0, (1.0 - intervention_effect))

                p = float(np.clip(p, 0.0, 0.99))
                # sample whether v reshapes
                if random.random() < p:
                    # sampling delay - lognormal (bursty human activity)
                    delay = float(np.random.lognormal(mean=0.2, sigma=1.0))
                    t_post = t + delay * dt

                    # determine v's reaction (model or bias)
                    if model_predictor:
                        model_pred = model_predictor(text, v)
                        stance = model_pred.get("stance")
                        sentiment = model_pred.get("sentiment")
                        if not stance:
                            stance, sentiment = sample_reaction_from_bias(v_attr)
                    else:
                        stance, sentiment = sample_reaction_from_bias(v_attr)

                    # mutate text with small probability
                    new_text = text
                    if random.random() < mutation_prob:
                        # very simple mutation: swap a noun or insert an adjective (placeholder)
                        new_text = mutate_text(text)

                    # schedule posting
                    self.events.append((t_post, 'post', v, u, new_text))
                    # mark tentative posted_time to avoid duplicate scheduling in same loop (some races still may exist)
                    self.G.nodes[v]["posted_time"] = t_post
                    self.G.nodes[v]["stance"] = stance
                    self.G.nodes[v]["sentiment"] = sentiment
                    self.G.nodes[v]["text"] = new_text

            # keep event queue sorted by time
            self.events.sort(key=lambda x: x[0])

            # record snapshot
            snap = self._compute_snapshot(t)
            self.timeline.append(snap)

        return self.timeline

    def _compute_snapshot(self, t):
        """Return statistics at time t"""
        posted = [n for n, d in self.G.nodes(data=True) if d.get("posted_time") is not None and d["posted_time"] <= t]
        size = len(posted)
        # stance/sentiment distributions
        stance_counts = defaultdict(int); sentiment_counts = defaultdict(int)
        for n in posted:
            s = self.G.nodes[n].get("stance") or "unknown"
            t_sent = self.G.nodes[n].get("sentiment") or "neutral"
            stance_counts[s] += 1
            sentiment_counts[t_sent] += 1
        stats = {
            "time": float(t),
            "cascade_size": size,
            "stance_counts": dict(stance_counts),
            "sentiment_counts": dict(sentiment_counts),
        }
        return stats

# -------------------------
# Simple mutation
# -------------------------
_MUTATIONS = [
    ("microchips", "nanobots"),
    ("vaccine", "injection"),
    ("chips", "trackers"),
    ("cause", "linked to"),
    ("secret", "hidden"),
]

def mutate_text(text):
    for a,b in _MUTATIONS:
        if a in text.lower():
            return text.lower().replace(a, b)
    # else add small phrase
    return text + " (unconfirmed)"





