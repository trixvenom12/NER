import osmnx as ox
import rasterio
import numpy as np
from shapely.geometry import LineString
import os

# Module 3: Building the road graph
ox.settings.useful_tags_way += ["ref", "bridge", "tunnel"]

BBOX = (26.60, 24.70, 93.30, 90.90) # N, S, E, W — corridor envelope

def build_graph():
    print("Downloading graph via OSMnx...")
    G = ox.graph_from_bbox(BBOX, network_type="drive", simplify=True)
    G = ox.truncate.largest_component(G, strongly=True)

    # attach mean slope from the DEM to every edge
    dem_path = os.path.join("..", "data", "dem", "srtm_ner.tif")
    
    if os.path.exists(dem_path):
        dem = rasterio.open(dem_path)
        
        def mean_slope(line: LineString) -> float:
            pts = [line.interpolate(d, normalized=True) for d in np.linspace(0, 1, 8)]
            try:
                z = np.array([next(dem.sample([(p.x, p.y)]))[0] for p in pts], dtype=float)
                seg_len = line.length * 111_000 / 7 # deg -> m, per sample gap
                return float(np.degrees(np.arctan(np.abs(np.diff(z)).mean() / max(seg_len, 1))))
            except Exception:
                return 0.0

        for u, v, k, d in G.edges(keys=True, data=True):
            d["mean_slope_deg"] = mean_slope(d["geometry"]) if "geometry" in d else 0.0
            
    # Save offline GraphML
    out_path = os.path.join("..", "data", "graph", "ner_drive.graphml")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    ox.save_graphml(G, out_path)
    print(f"Graph saved to {out_path}")

if __name__ == "__main__":
    build_graph()
