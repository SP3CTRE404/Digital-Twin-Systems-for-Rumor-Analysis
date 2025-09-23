import numpy as np
from scipy import stats
import networkx as nx


def cascade_size(timeline):
    return [snap.get("cascade_size", 0) for snap in (timeline or [])]


def time_to_peak(timeline):
    sizes = cascade_size(timeline)
    if not sizes:
        return None
    peak_idx = int(np.argmax(sizes))
    return timeline[peak_idx].get("time")


def compute_Rt(timeline, window=3):
    """
    Compute simple R_t: avg new posts per existing poster in sliding window
    """
    sizes = cascade_size(timeline)
    Rt = []
    for i in range(1, len(sizes)):
        new = sizes[i] - sizes[i - 1]
        prev = sizes[i - 1] if sizes[i - 1] > 0 else 1
        Rt.append(new / prev)
    return Rt


def compare_distribution(real_vals, sim_vals):
    """
    KS test between two numeric arrays
    Returns ks_stat, pvalue
    """
    return stats.ks_2samp(real_vals, sim_vals)


def graph_statistics(G):
    deg_hist = [d for _, d in G.degree()]
    return {
        "avg_clustering": nx.average_clustering(G.to_undirected()),
        "degree_mean": float(np.mean(deg_hist) if deg_hist else 0.0),
        "degree_std": float(np.std(deg_hist) if deg_hist else 0.0),
    }






