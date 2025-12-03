def score_transit(transit: dict) -> float:
    nature = (transit.get("impact_area") or "").lower()
    risk = (transit.get("risk_level") or "").lower()

    base = 10
    if risk == "high":
        base = 30
    elif risk == "moderate":
        base = 20

    if "burnout" in nature or "stress" in nature:
        base += 10

    return base


def compute_transit_pressure(transits: list) -> float:
    if not transits:
        return 0.0
    scores = [score_transit(t) for t in transits]
    avg = sum(scores) / len(scores)
    return min(avg, 100.0)

