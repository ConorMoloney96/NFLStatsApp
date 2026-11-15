"""Produce chronological NFL Elo forecasts from nflverse schedule data."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import nflreadpy

HOME_ADVANTAGE = 55
K = 20
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "predictions.json"

def probability(home, away):
    return 1 / (1 + 10 ** (-(home + HOME_ADVANTAGE - away) / 400))

def score(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None

def main():
    now = datetime.now(timezone.utc)
    raw = nflreadpy.load_schedules(True).to_dicts()
    rows = []
    for g in raw:
        try:
            season = int(g["season"])
            if not 2015 <= season <= now.year or g.get("game_type") != "REG":
                continue
            if not g.get("home_team") or not g.get("away_team"):
                continue
            day = str(g["gameday"])
            clock = str(g.get("gametime") or "12:00")
            kickoff = datetime.fromisoformat(day + "T" + clock).replace(tzinfo=ZoneInfo("America/New_York")).astimezone(timezone.utc)
            rows.append((kickoff, g))
        except (KeyError, TypeError, ValueError):
            continue
    rows.sort(key=lambda item: (item[0], str(item[1].get("game_id", ""))))
    if len(rows) < 500:
        raise RuntimeError("Insufficient schedule data; refusing to overwrite last published forecasts")
    ratings, output = {}, []
    previous_season = None
    evaluated = correct = 0
    brier = 0.0
    for kickoff, g in rows:
        season = int(g["season"])
        if previous_season is not None and season != previous_season:
            ratings = {team: 1500 + .7 * (rating - 1500) for team, rating in ratings.items()}
        previous_season = season
        home, away = str(g["home_team"]), str(g["away_team"])
        hr, ar = ratings.get(home, 1500.0), ratings.get(away, 1500.0)
        p = probability(hr, ar)
        hs, aws = score(g.get("home_score")), score(g.get("away_score"))
        final = hs is not None and aws is not None and kickoff < now
        if season >= now.year - 1:
            output.append({
                "game_id": str(g.get("game_id") or f"{season}-{g.get('week')}-{away}-{home}"),
                "season": season, "week": int(g.get("week") or 0),
                "kickoff": kickoff.isoformat().replace("+00:00", "Z"),
                "home_team": home, "away_team": away, "home_name": home, "away_name": away,
                "home_elo": round(hr), "away_elo": round(ar), "home_probability": round(p, 4),
                "status": "final" if final else "scheduled",
                "home_score": int(hs) if final else None, "away_score": int(aws) if final else None
            })
        if final:
            result = 1.0 if hs > aws else 0.0 if hs < aws else .5
            if season >= 2023 and hs != aws:
                evaluated += 1
                correct += int((p >= .5) == (hs > aws))
                brier += (p - result) ** 2
            factor = math.log1p(abs(hs - aws)) * 2.2 / (2.2 + abs(hr - ar) * .001)
            change = K * factor * (result - p)
            ratings[home] = hr + change
            ratings[away] = ar - change
    if not output:
        raise RuntimeError("No predictions generated")
    payload = {
        "mode": "historical", "generated_at": now.isoformat(),
        "performance": {
            "evaluated_games": evaluated,
            "winner_accuracy": round(correct / evaluated, 4) if evaluated else None,
            "brier_score": round(brier / evaluated, 4) if evaluated else None
        },
        "games": output
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    print(f"Generated {len(output)} games, evaluated {evaluated} games")

if __name__ == "__main__":
    main()
