"""Quick diagnostic: test route divergence across profiles."""
import networkx as nx
import json
import sqlite3
from api.services.routing_engine import route_single, route_all_alternatives

G = nx.read_graphml("data/graph/ner_drive.graphml", node_type=int)
if not isinstance(G, nx.MultiDiGraph):
    G = nx.MultiDiGraph(G)
print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
print(f"Graph type: {type(G).__name__}")

# Load risk cache
conn = sqlite3.connect("data/ner_logistics.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT segment_id, score, band, factors FROM segment_risk WHERE computed_at = (SELECT MAX(computed_at) FROM segment_risk);")
rows = cur.fetchall()
risk_cache = {}
for r in rows:
    risk_cache[r["segment_id"]] = {"score": r["score"], "band": r["band"], "factors": json.loads(r["factors"])}
conn.close()
print(f"Risk cache: {len(risk_cache)} segments")

# Show high-risk segments
print("\n--- HIGH RISK SEGMENTS (score > 40) ---")
for sid, info in sorted(risk_cache.items()):
    if info["score"] > 40:
        print(f"  Seg {sid}: score={info['score']:.1f}, band={info['band']}")

# Route all profiles
print("\n--- ROUTING RESULTS (101 -> 127) ---")
result = route_all_alternatives(G, 101, 127, risk_cache, [])
for profile in ["fastest", "balanced", "safest"]:
    r = result["routes"][profile]
    if r.get("path_found"):
        print(f"  {profile}: dist={r['distance_km']}km, dur={r['duration_min']}min, mean_risk={r['mean_risk']}, max_risk={r['max_risk']}")
        print(f"    nodes: {r['node_ids']}")
    else:
        print(f"  {profile}: NO PATH - {r.get('error')}")

# Also test different origin/destination
print("\n--- ROUTING RESULTS (108 -> 127) Shillong -> Silchar ---")
result2 = route_all_alternatives(G, 108, 127, risk_cache, [])
for profile in ["fastest", "balanced", "safest"]:
    r = result2["routes"][profile]
    if r.get("path_found"):
        print(f"  {profile}: dist={r['distance_km']}km, dur={r['duration_min']}min, mean_risk={r['mean_risk']}, max_risk={r['max_risk']}")
        print(f"    nodes: {r['node_ids']}")
    else:
        print(f"  {profile}: NO PATH - {r.get('error')}")
