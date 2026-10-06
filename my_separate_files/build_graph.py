"""
build/build_graph.py — Builds the NH-6 Corridor Routable Road Graph
Covers NH-6: Guwahati (Khanapara) -> Shillong -> Silchar (~350 km)
Bounding Box: N: 26.60, S: 24.70, E: 93.30, W: 90.90

Generates:
1. data/graph/ner_drive.graphml (NetworkX GraphML)
2. Seed data for the 'segment' table in database
"""

import os
import json
import math
import networkx as nx
from shapely.geometry import LineString

# Waypoints along NH-6 and alternative bypasses
CORRIDOR_NODES = [
    # Main NH-6 Corridor Backbone
    {"id": 101, "name": "Guwahati_Khanapara", "lat": 26.1150, "lon": 91.8210, "elevation_m": 55},
    {"id": 102, "name": "Byrnihat_Checkpost", "lat": 26.0420, "lon": 91.8650, "elevation_m": 90},
    {"id": 103, "name": "Nongpoh_North", "lat": 25.9320, "lon": 91.8780, "elevation_m": 485},
    {"id": 104, "name": "Nongpoh_Town", "lat": 25.9012, "lon": 91.8805, "elevation_m": 520},
    {"id": 105, "name": "Umsning_Junction", "lat": 25.7620, "lon": 91.9051, "elevation_m": 790},
    
    # Branch A: Through Shillong City
    {"id": 106, "name": "Umiam_Barapani", "lat": 25.6610, "lon": 91.8980, "elevation_m": 1020},
    {"id": 107, "name": "Mawiong_Shillong", "lat": 25.6020, "lon": 91.8830, "elevation_m": 1420},
    {"id": 108, "name": "Shillong_Central", "lat": 25.5788, "lon": 91.8933, "elevation_m": 1525},
    {"id": 109, "name": "Laitkor_Ghat", "lat": 25.5350, "lon": 91.9320, "elevation_m": 1680},
    {"id": 110, "name": "Mawryngkneng_Junction", "lat": 25.5560, "lon": 92.0520, "elevation_m": 1390},
    
    # Branch B: Shillong Bypass (Fast freight trunk avoiding city)
    {"id": 111, "name": "Shillong_Bypass_Mid", "lat": 25.6320, "lon": 91.9850, "elevation_m": 1210},
    
    # East Jaintia Hills & Coal / Limestone Ghats
    {"id": 112, "name": "Ummulong", "lat": 25.4950, "lon": 92.1240, "elevation_m": 1340},
    {"id": 113, "name": "Jowai_Bypass", "lat": 25.4410, "lon": 92.2030, "elevation_m": 1380},
    {"id": 114, "name": "Khliehtyrshi", "lat": 25.4120, "lon": 92.2450, "elevation_m": 1310},
    {"id": 115, "name": "Ladrymbai", "lat": 25.3210, "lon": 92.3120, "elevation_m": 1250},
    {"id": 116, "name": "Khliehriat", "lat": 25.2640, "lon": 92.3520, "elevation_m": 1180},
    {"id": 117, "name": "Lumshnong_Quarry", "lat": 25.1850, "lon": 92.3780, "elevation_m": 620},
    
    # The Critical Sonapur Pinch Point & Ghat
    {"id": 118, "name": "Sonapur_Tunnel_North", "lat": 25.1180, "lon": 92.3650, "elevation_m": 310},
    {"id": 119, "name": "Sonapur_Tunnel_South", "lat": 25.1110, "lon": 92.3720, "elevation_m": 260},
    
    # Alternative Sonapur / Malidor Escarpment Detour (High mountain ridge bypass)
    {"id": 120, "name": "Sonapur_Ridge_Detour", "lat": 25.1290, "lon": 92.3920, "elevation_m": 580},
    
    # Border into Assam Barak Valley
    {"id": 121, "name": "Malidor_Border", "lat": 25.0420, "lon": 92.4210, "elevation_m": 140},
    {"id": 122, "name": "Umkiang", "lat": 25.0680, "lon": 92.3850, "elevation_m": 190},
    {"id": 123, "name": "Kalain_Junction", "lat": 24.9650, "lon": 92.5620, "elevation_m": 45},
    {"id": 124, "name": "Badarpur_Ghat", "lat": 24.9020, "lon": 92.5850, "elevation_m": 25},
    {"id": 125, "name": "Panchgram", "lat": 24.8720, "lon": 92.6510, "elevation_m": 22},
    {"id": 126, "name": "Silchar_Ramnagar", "lat": 24.8380, "lon": 92.7420, "elevation_m": 26},
    {"id": 127, "name": "Silchar_ISBT", "lat": 24.8250, "lon": 92.7910, "elevation_m": 25},
    
    # Alternative Valley North Bypass: Kalain -> Borkhola -> Silchar
    {"id": 128, "name": "Borkhola_Bypass", "lat": 24.9120, "lon": 92.7210, "elevation_m": 30}
]

# Map node lookup
NODE_MAP = {n["id"]: n for n in CORRIDOR_NODES}

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000  # radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Edge connections defining the corridor road network
CORRIDOR_EDGES = [
    # Guwahati to Umsning
    (101, 102, "NH-6", "trunk", 50, 0.12),
    (102, 103, "NH-6", "trunk", 50, 0.22),
    (103, 104, "NH-6", "trunk", 45, 0.18),
    (104, 105, "NH-6", "trunk", 45, 0.25),
    
    # Umsning -> Shillong -> Mawryngkneng (Main city route)
    (105, 106, "NH-6", "trunk", 40, 0.38),
    (106, 107, "NH-6", "trunk", 35, 0.42),
    (107, 108, "GS-Road", "primary", 30, 0.20),
    (108, 109, "Jowai-Road", "primary", 35, 0.32),
    (109, 110, "NH-6", "trunk", 40, 0.35),
    
    # Umsning -> Shillong Bypass -> Mawryngkneng (Freight bypass)
    (105, 111, "Shillong-Bypass", "trunk", 60, 0.18),
    (111, 110, "Shillong-Bypass", "trunk", 60, 0.20),
    
    # Mawryngkneng to Jowai to Khliehriat
    (110, 112, "NH-6", "trunk", 45, 0.24),
    (112, 113, "NH-6", "trunk", 45, 0.28),
    (113, 114, "NH-6", "trunk", 45, 0.25),
    (114, 115, "NH-6", "trunk", 40, 0.32),
    (115, 116, "NH-6", "trunk", 40, 0.30),
    (116, 117, "NH-6", "trunk", 35, 0.58), # steep descent to Lumshnong
    
    # Lumshnong to Sonapur (THE HIGH HAZARD SLIDE CORRIDOR)
    (117, 118, "NH-6", "trunk", 35, 0.65),
    (118, 119, "NH-6-Sonapur-Tunnel", "trunk", 30, 0.88), # The tunnel slide cut
    
    # Sonapur Detour Route (High ridge bypass used during tunnel blockades)
    (117, 120, "Sonapur-Old-Ridge-Detour", "secondary", 34, 0.18),
    (120, 119, "Sonapur-Old-Ridge-Detour", "secondary", 34, 0.20),
    
    # Sonapur to Malidor to Kalain
    (119, 122, "NH-6", "trunk", 35, 0.60),
    (122, 121, "NH-6", "trunk", 35, 0.55),
    (121, 123, "NH-6", "trunk", 40, 0.35),
    
    # Kalain to Silchar via Badarpur & Panchgram (Main route)
    (123, 124, "NH-6", "trunk", 48, 0.40),
    (124, 125, "NH-6", "trunk", 48, 0.38),
    (125, 126, "NH-6", "trunk", 48, 0.15),
    (126, 127, "NH-6", "trunk", 40, 0.08),
    
    # Alternative Valley Detour: Kalain -> Borkhola -> Silchar
    (123, 128, "Borkhola-Link", "secondary", 46, 0.10),
    (128, 126, "Borkhola-Silchar", "secondary", 46, 0.08)
]

def build_graph():
    G = nx.MultiDiGraph()
    segments_data = []
    
    # Add nodes
    for n in CORRIDOR_NODES:
        G.add_node(
            n["id"],
            name=n["name"],
            y=n["lat"],
            x=n["lon"],
            elevation_m=n["elevation_m"]
        )
    
    seg_id = 1
    # Add bidirectional edges
    for u, v, road_ref, highway, speed_kph, base_susc in CORRIDOR_EDGES:
        n_u = NODE_MAP[u]
        n_v = NODE_MAP[v]
        
        # Calculate length
        length_m = round(haversine_m(n_u["lat"], n_u["lon"], n_v["lat"], n_v["lon"]) * 1.18, 1) # winding road factor
        
        # Calculate mean slope in degrees from elevation profile
        elev_diff = abs(n_v["elevation_m"] - n_u["elevation_m"])
        mean_slope_deg = round(math.degrees(math.atan2(elev_diff, max(length_m, 1))), 1)
        
        # For mountainous ghat stretches, ensure realistic slope literature values
        if "Sonapur" in road_ref or "Lumshnong" in n_u["name"] or "Lumshnong" in n_v["name"]:
            mean_slope_deg = max(mean_slope_deg, 31.5)
        elif "Ghat" in n_u["name"] or "Ghat" in n_v["name"] or "Ridge" in road_ref:
            mean_slope_deg = max(mean_slope_deg, 24.0)
        
        # Geometries
        line_forward = LineString([(n_u["lon"], n_u["lat"]), (n_v["lon"], n_v["lat"])])
        line_backward = LineString([(n_v["lon"], n_v["lat"]), (n_u["lon"], n_u["lat"])])
        
        # Forward edge
        edge_data_fwd = {
            "segment_id": seg_id,
            "osm_way_id": 100000 + seg_id,
            "road_ref": road_ref,
            "highway": highway,
            "length": length_m,
            "speed_kph": speed_kph,
            "mean_slope_deg": mean_slope_deg,
            "susceptibility": base_susc,
            "geometry": line_forward.wkt,
            "u": u,
            "v": v
        }
        G.add_edge(u, v, key=0, **edge_data_fwd)
        segments_data.append({
            "id": seg_id,
            "osm_way_id": 100000 + seg_id,
            "u_node": u,
            "v_node": v,
            "road_ref": road_ref,
            "highway": highway,
            "length_m": length_m,
            "free_speed_kph": speed_kph,
            "mean_slope_deg": mean_slope_deg,
            "susceptibility": base_susc,
            "geom": {"type": "LineString", "coordinates": [[n_u["lon"], n_u["lat"]], [n_v["lon"], n_v["lat"]]]}
        })
        seg_id += 1
        
        # Reverse edge
        edge_data_rev = {
            "segment_id": seg_id,
            "osm_way_id": 100000 + seg_id,
            "road_ref": road_ref,
            "highway": highway,
            "length": length_m,
            "speed_kph": speed_kph,
            "mean_slope_deg": mean_slope_deg,
            "susceptibility": base_susc,
            "geometry": line_backward.wkt,
            "u": v,
            "v": u
        }
        G.add_edge(v, u, key=0, **edge_data_rev)
        segments_data.append({
            "id": seg_id,
            "osm_way_id": 100000 + seg_id,
            "u_node": v,
            "v_node": u,
            "road_ref": road_ref,
            "highway": highway,
            "length_m": length_m,
            "free_speed_kph": speed_kph,
            "mean_slope_deg": mean_slope_deg,
            "susceptibility": base_susc,
            "geom": {"type": "LineString", "coordinates": [[n_v["lon"], n_v["lat"]], [n_u["lon"], n_u["lat"]]]}
        })
        seg_id += 1

    os.makedirs("data/graph", exist_ok=True)
    graphml_path = "data/graph/ner_drive.graphml"
    nx.write_graphml(G, graphml_path)
    print(f"[OK] Graph constructed: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges saved to {graphml_path}")
    
    # Also dump segments JSON for DB seeding
    with open("data/segments_seed.json", "w") as f:
        json.dump(segments_data, f, indent=2)
    print(f"[OK] Segments seed saved: {len(segments_data)} road segments")
    
    return G

if __name__ == "__main__":
    build_graph()
