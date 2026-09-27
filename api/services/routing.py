import networkx as nx

# Module 5: Hazard-aware routing
PROFILES = {"fastest": 0.0, "balanced": 1.2, "safest": 4.0}

def edge_cost(alpha, risk_by_seg):
    def w(u, v, data):
        # Base time cost in minutes
        base_min = data.get("length", 100) / 1000 / max(data.get("speed_kph", 40), 5) * 60
        
        # Risk is a 0..1 ratio where 1.0 is 100 risk score
        r = risk_by_seg.get(data.get("segment_id", 0), 0.0) / 100.0
        
        # Confirmed blockade semantics -> NetworkX removes edge
        if r >= 0.92:
            return None
            
        # Squared risk term: mildly damp road doesn't get abandoned, 
        # while genuinely dangerous ghat section dominates.
        return base_min * (1 + alpha * r ** 2)
    return w

def route(G, src, dst, profile, risk_by_seg):
    w = edge_cost(PROFILES[profile], risk_by_seg)
    try:
        path = nx.shortest_path(G, src, dst, weight=w)
        return path
    except nx.NetworkXNoPath:
        return None
