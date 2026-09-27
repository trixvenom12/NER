from dataclasses import dataclass, asdict

# Module 4: The risk scoring engine

WEIGHTS = {"rain": .34, "slope": .22, "susceptibility": .18, "history": .16, "reports": .10}

def norm(x, lo, hi):
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))

@dataclass
class Factors:
    rain: float
    slope: float
    susceptibility: float
    history: float
    reports: float

def score_segment(seg, wx, hist_count, active_reports) -> tuple[float, dict]:
    # wx is weather observation for the segment
    # seg is the row from segment table / graph edge data
    
    # Defaults in case of missing data
    rain_24h_mm = wx.get('rain_24h_mm', 0) if wx else 0
    mean_slope_deg = seg.get('mean_slope_deg', 0)
    susceptibility = seg.get('susceptibility', 0)
    
    f = Factors(
        rain = norm(rain_24h_mm, 10, 120),          # IMD heavy-rain thresholds
        slope = norm(mean_slope_deg, 8, 35),
        susceptibility = susceptibility or 0.0,
        history = norm(hist_count, 0, 6),
        reports = norm(active_reports, 0, 3),
    )
    
    raw = sum(WEIGHTS[k] * v for k, v in asdict(f).items())
    return round(raw * 100, 1), asdict(f)

def band(score):
    return "hazard" if score >= 62 else "caution" if score >= 34 else "safe"

def adjusted(base_score, prob):
    """Model nudges the transparent index by at most 15 points."""
    return max(0.0, min(100.0, base_score + (prob - 0.5) * 30))
