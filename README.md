# NFL Predict MVP

A mobile-friendly static NFL Elo prediction dashboard, deployed via GitHub Pages.

## Live site

https://conormoloney96.github.io/NFLStatsApp/

## Features
- Week/season selector and game forecasts
- Pre-game Elo ratings and home/away win probabilities
- Chronological historical evaluation (winner accuracy and Brier score)
- Daily GitHub Actions update using nflverse schedules

The initial data file contains **synthetic demonstration matchups**, prominently labelled. Run **Actions → Refresh NFL data → Run workflow** to replace it with historical data and current schedule predictions. The model is experimental, uncalibrated and not betting advice.

## GitHub Pages
Settings → Pages → Build and deployment → Deploy from a branch → main → /(root).

## Local development
```bash
pip install -r requirements.txt
python scripts/update_predictions.py
python -m http.server 8000
```
Visit http://localhost:8000. The site is static and requires no API keys or database.

Source data: https://github.com/nflverse/nflverse-data. Check source licensing before commercial reuse.
